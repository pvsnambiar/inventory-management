from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class RestockingRecommendationRequest(BaseModel):
    budget: float
    warehouse: Optional[str] = 'all'
    category: Optional[str] = 'all'

class RecommendedItem(BaseModel):
    sku: str
    name: str
    category: str
    forecasted_demand: int
    unit_cost: float
    recommended_quantity: int
    item_total_cost: float

class RestockingRecommendationResponse(BaseModel):
    recommended_items: List[RecommendedItem]
    total_cost: float
    budget_used_percent: float
    budget_remaining: float

class OrderItemRequest(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_price: float

class CreateOrderRequest(BaseModel):
    items: List[OrderItemRequest]
    order_type: Optional[str] = 'regular'

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        has_po = any(po["backlog_item_id"] == item["id"] for po in purchase_orders)
        item_dict["has_purchase_order"] = has_po
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

@app.post("/api/restocking/recommend", response_model=RestockingRecommendationResponse)
def get_restocking_recommendations(request: RestockingRecommendationRequest):
    """Get restocking recommendations based on demand forecast and budget"""
    budget = request.budget
    warehouse_filter = request.warehouse
    category_filter = request.category

    if budget <= 0:
        return RestockingRecommendationResponse(
            recommended_items=[],
            total_cost=0.0,
            budget_used_percent=0.0,
            budget_remaining=budget
        )

    # Create a map of SKU to inventory item for quick lookup
    inventory_map = {item['sku']: item for item in inventory_items}

    # Filter demand forecasts and sort by forecasted_demand (high demand first)
    filtered_forecasts = []
    for forecast in demand_forecasts:
        # Check if inventory item exists for this forecast
        if forecast['item_sku'] not in inventory_map:
            continue
        filtered_forecasts.append(forecast)

    # Sort by forecasted_demand descending
    filtered_forecasts.sort(key=lambda x: x['forecasted_demand'], reverse=True)

    # Build recommendation list until budget is exhausted
    recommended_items = []
    remaining_budget = budget
    total_cost = 0.0

    for forecast in filtered_forecasts:
        inventory_item = inventory_map[forecast['item_sku']]

        # Apply warehouse and category filters
        if warehouse_filter != 'all' and inventory_item.get('warehouse') != warehouse_filter:
            continue
        if category_filter != 'all' and inventory_item.get('category', '').lower() != category_filter.lower():
            continue

        unit_cost = inventory_item['unit_cost']
        if unit_cost <= 0:
            continue

        # Calculate recommended quantity
        max_qty_by_budget = int(remaining_budget / unit_cost)
        recommended_qty = min(forecast['forecasted_demand'], max_qty_by_budget)

        if recommended_qty <= 0:
            continue

        item_total_cost = recommended_qty * unit_cost
        remaining_budget -= item_total_cost
        total_cost += item_total_cost

        recommended_items.append(RecommendedItem(
            sku=forecast['item_sku'],
            name=forecast['item_name'],
            category=inventory_item.get('category', 'Unknown'),
            forecasted_demand=forecast['forecasted_demand'],
            unit_cost=unit_cost,
            recommended_quantity=recommended_qty,
            item_total_cost=item_total_cost
        ))

    budget_used_percent = (total_cost / budget * 100) if budget > 0 else 0.0

    return RestockingRecommendationResponse(
        recommended_items=recommended_items,
        total_cost=total_cost,
        budget_used_percent=round(budget_used_percent, 2),
        budget_remaining=round(remaining_budget, 2)
    )

@app.post("/api/orders", response_model=Order)
def create_order(request: CreateOrderRequest):
    """Create a new order (regular or restocking)"""
    if not request.items or len(request.items) == 0:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    # Generate new order ID and number
    max_order_id = max([int(order['id']) for order in orders], default=0)
    new_order_id = str(max_order_id + 1)

    if request.order_type == 'restocking':
        new_order_number = f"ORD-RESTOCK-2025-{len([o for o in orders if 'RESTOCK' in o.get('order_number', '')]) + 1:04d}"
        customer = "Internal - Restocking Order"
    else:
        new_order_number = f"ORD-2025-{len(orders) + 1:04d}"
        customer = "Manual Order"

    # Calculate total value and prepare items
    total_value = 0.0
    items = []
    for item in request.items:
        item_total = item.quantity * item.unit_price
        total_value += item_total
        items.append({
            "sku": item.sku,
            "name": item.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        })

    # Create order with delivery date
    now = datetime.now()
    order_date = now.isoformat()
    expected_delivery = (now + timedelta(days=7)).isoformat()

    new_order = {
        "id": new_order_id,
        "order_number": new_order_number,
        "customer": customer,
        "items": items,
        "status": "Restocking" if request.order_type == 'restocking' else "Processing",
        "order_date": order_date,
        "expected_delivery": expected_delivery,
        "total_value": round(total_value, 2),
        "actual_delivery": None,
        "warehouse": "All",
        "category": "Mixed"
    }

    # Add to orders list
    orders.append(new_order)

    return Order(**new_order)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
