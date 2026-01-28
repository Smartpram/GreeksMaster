from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from app.config import Config
import json

DATABASE_URL = Config.DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class GTTOrder(Base):
    __tablename__ = 'gtt_orders'
    id = Column(Integer, primary_key=True, index=True)
    gtt_order_id = Column(String, index=True)
    fresh_order_id = Column(String, nullable=True)
    exchange_code = Column(String, nullable=True)
    product_type = Column(String, nullable=True)
    stock_code = Column(String, nullable=True)
    expiry_date = Column(String, nullable=True)
    strike_price = Column(Float, nullable=True)
    right = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    index_or_stock = Column(String, nullable=True)
    gtt_type = Column(String, nullable=True)
    order_datetime = Column(DateTime, nullable=True)
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    legs = relationship('GTTOrderLeg', back_populates='order', cascade='all, delete-orphan')


class GTTOrderLeg(Base):
    __tablename__ = 'gtt_order_legs'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('gtt_orders.id'), nullable=False)
    gtt_leg_type = Column(String, nullable=True)
    action = Column(String, nullable=True)
    trigger_price = Column(Float, nullable=True)
    limit_price = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    leg_gtt_order_id = Column(String, nullable=True)
    raw = Column(Text, nullable=True)

    order = relationship('GTTOrder', back_populates='legs')


def init_db():
    Base.metadata.create_all(bind=engine)


def insert_gtt_records(success_list):
    """Insert a list of GTT records (from API response) into the DB.

    Returns: list of inserted GTTOrder IDs
    """
    db = SessionLocal()
    inserted = []
    try:
        for gtt in success_list:
            # Normalize order_datetime
            odt = None
            odt_raw = gtt.get('order_datetime')
            if odt_raw:
                for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y"):
                    try:
                        odt = datetime.strptime(odt_raw, fmt)
                        break
                    except Exception:
                        continue

            order = GTTOrder(
                gtt_order_id=None,
                fresh_order_id=gtt.get('fresh_order_id'),
                exchange_code=gtt.get('exchange_code'),
                product_type=gtt.get('product_type'),
                stock_code=gtt.get('stock_code'),
                expiry_date=gtt.get('expiry_date'),
                strike_price=gtt.get('strike_price'),
                right=gtt.get('right'),
                quantity=gtt.get('quantity'),
                index_or_stock=gtt.get('index_or_stock'),
                gtt_type=gtt.get('gtt_type'),
                order_datetime=odt,
                raw_payload=json.dumps(gtt, default=str)
            )

            # Take gtt_order_id from first leg if present
            details = gtt.get('order_details', []) or []
            gid = None
            for leg in details:
                gid = gid or leg.get('gtt_order_id')
            order.gtt_order_id = gid

            db.add(order)
            db.flush()  # populate order.id

            for leg in details:
                leg_obj = GTTOrderLeg(
                    order_id=order.id,
                    gtt_leg_type=leg.get('gtt_leg_type'),
                    action=leg.get('action'),
                    trigger_price=leg.get('trigger_price'),
                    limit_price=leg.get('limit_price'),
                    status=leg.get('status'),
                    leg_gtt_order_id=leg.get('gtt_order_id'),
                    raw=json.dumps(leg, default=str)
                )
                db.add(leg_obj)

            db.commit()
            inserted.append(order.id)

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return inserted


def fetch_table_ready_payload(limit: int = 100, status: str = None, instrument: str = None, gtt_order_id: str = None, page: int = 1, per_page: int = 25):
    """Return expanded legs + summary status suitable for a table UI.

    Supports simple filtering by status/instrument/gtt_order_id and pagination.
    """
    db = SessionLocal()
    try:
        q = db.query(GTTOrder).order_by(GTTOrder.created_at.desc())
        if gtt_order_id:
            q = q.filter(GTTOrder.gtt_order_id == gtt_order_id)
        if instrument:
            q = q.filter(GTTOrder.stock_code.ilike(f"%{instrument}%"))

        total = q.count()
        # pagination
        if per_page <= 0:
            per_page = 25
        if page <= 0:
            page = 1

        q = q.offset((page-1) * per_page).limit(per_page)
        orders = q.all()

        out = []
        for o in orders:
            legs = []
            all_statuses = set()
            for l in o.legs:
                legs.append({
                    'gtt_leg_type': l.gtt_leg_type,
                    'action': l.action,
                    'trigger_price': l.trigger_price,
                    'limit_price': l.limit_price,
                    'status': l.status,
                })
                if l.status:
                    all_statuses.add(l.status.lower())

            if not all_statuses:
                status_summary = 'Unknown'
            elif all(s == 'cancelled' for s in all_statuses):
                status_summary = 'All Cancelled'
            elif all(s == 'filled' for s in all_statuses):
                status_summary = 'All Filled'
            else:
                status_summary = 'Mixed'

            out.append({
                'id': o.id,
                'gtt_order_id': o.gtt_order_id,
                'fresh_order_id': o.fresh_order_id,
                'instrument': f"{o.stock_code} {o.expiry_date} {int(o.strike_price) if o.strike_price else ''} {o.right or ''}",
                'quantity': o.quantity,
                'gtt_type': o.gtt_type,
                'order_datetime': o.order_datetime.isoformat() if o.order_datetime else None,
                'status_summary': status_summary,
                'legs': legs,
            })

        return {'total': total, 'page': page, 'per_page': per_page, 'items': out}
    finally:
        db.close()


def fetch_raw_payloads(limit: int = 100):
    """Return raw payloads for escalation bundle (most recent first)."""
    db = SessionLocal()
    try:
        orders = db.query(GTTOrder).order_by(GTTOrder.created_at.desc()).limit(limit).all()
        out = []
        for o in orders:
            out.append({
                'id': o.id,
                'gtt_order_id': o.gtt_order_id,
                'created_at': o.created_at.isoformat(),
                'raw_payload': json.loads(o.raw_payload) if o.raw_payload else None
            })
        return out
    finally:
        db.close()
