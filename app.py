from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__, static_folder='static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:yourpassword@127.0.0.1:3306/yourdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Articles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    stock_quantity = db.Column(db.Integer, default=0)
    minimum_threshold = db.Column(db.Integer, default=0)
    location = db.Column(db.String(255))

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_date = db.Column(db.Date, nullable=False)
    inventory_type = db.Column(db.String(50))  # 'Complete' or 'Partial'
    status = db.Column(db.String(50), default='Active')
    justification = db.Column(db.Text)

class InventoryItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    recorded_quantity = db.Column(db.Integer, nullable=False)
    actual_quantity = db.Column(db.Integer, nullable=False)
    discrepancy = db.Column(db.Integer)

class Reports(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(100), nullable=False)
    data = db.Column(db.Text, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

class StockMovements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(50))  # 'Entrée' or 'Sortie'
    reason = db.Column(db.Text, nullable=False)
    movement_date = db.Column(db.Date, default=datetime.utcnow)

class SupplierArticles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)

class Suppliers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    contact_details = db.Column(db.Text)
    status = db.Column(db.String(50), default='Active')

class SystemLogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False)

# Routes
@app.route('/')
def dashboard():
    total_articles = Articles.query.count()
    total_stock = db.session.query(db.func.sum(Articles.stock_quantity)).scalar() or 0
    critical_articles = Articles.query.filter(Articles.stock_quantity < Articles.minimum_threshold).all()
    suppliers_count = Suppliers.query.count()
    recent_movements = StockMovements.query.order_by(StockMovements.movement_date.desc()).limit(5).all()
    
    return render_template('dashboard.html', total_articles=total_articles,
                           total_stock=total_stock, critical_articles=critical_articles,
                           suppliers_count=suppliers_count, recent_movements=recent_movements)

@app.route('/articles')
def articles():
    articles = Articles.query.all()
    return render_template('articles/list.html', articles=articles)

@app.route('/articles/new', methods=['GET', 'POST'])
def new_article():
    if request.method == 'POST':
        code = request.form['code']
        name = request.form['name']
        category = request.form['category']
        stock_quantity = request.form['stock_quantity']
        minimum_threshold = request.form['minimum_threshold']
        location = request.form['location']

        article = Articles(code=code, name=name, category=category, stock_quantity=stock_quantity,
                          minimum_threshold=minimum_threshold, location=location)
        db.session.add(article)
        db.session.commit()
        return redirect(url_for('articles'))
    return render_template('articles/new.html')

@app.route('/articles/edit/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    article = Articles.query.get_or_404(article_id)
    if request.method == 'POST':
        article.code = request.form['code']
        article.name = request.form['name']
        article.category = request.form['category']
        article.stock_quantity = request.form['stock_quantity']
        article.minimum_threshold = request.form['minimum_threshold']
        article.location = request.form['location']
        
        db.session.commit()
        return redirect(url_for('articles'))
    return render_template('articles/edit.html', article=article)

@app.route('/articles/delete/<int:article_id>', methods=['POST'])
def delete_article(article_id):
    article = Articles.query.get_or_404(article_id)
    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('articles'))

@app.route('/stock')
def stock():
    return render_template('stock/stock_tabs.html')

from datetime import datetime

@app.route('/stock/movements', methods=['GET'])
def stock_movements():
    # Get filter parameters from query string
    filter_type = request.args.get('type', None)
    filter_date = request.args.get('date', None)

    # Build the base query
    query = StockMovements.query

    # Apply movement type filter if present
    if filter_type:
        query = query.filter_by(movement_type=filter_type)

    # Apply date filter if present
    if filter_date:
        try:
            # Parse the date from the query string
            date_obj = datetime.strptime(filter_date, '%Y-%m-%d').date()
            query = query.filter(db.func.date(StockMovements.movement_date) == date_obj)
        except ValueError:
            # Handle invalid date formats gracefully
            pass

    # Fetch the filtered movements
    movements = query.all()

    return render_template('stock/movements.html', movements=movements, filter_type=filter_type, filter_date=filter_date)

@app.route('/stock/inventory', methods=['GET'])
def inventory_main():
    """Main inventory page with tabs."""
    return render_template('stock/inventory_tabs.html')

@app.route('/stock/inventory/current', methods=['GET'])
def current_inventory():
    """View for the current inventory."""
    inventories = Inventory.query.filter_by(status='Active').all()

    # Add dynamic data for each inventory
    inventory_data = []
    total_comptes = 0
    total_ecarts = 0

    for inventory in inventories:
        items = InventoryItems.query.filter_by(inventory_id=inventory.id).all()
        total_articles = len(items)
        discrepancies = sum(1 for item in items if item.actual_quantity < item.recorded_quantity)
        comptes = sum(1 for item in items if item.actual_quantity >= item.recorded_quantity)

        total_comptes += comptes
        total_ecarts += discrepancies

        inventory_data.append({
            'inventory': inventory,
            'total_articles': total_articles,
            'discrepancies': discrepancies,
            'comptes': comptes,
            'items': items  # Add inventory items for table rendering
        })

    return render_template(
        'stock/current_inventory.html',
        inventory_data=inventory_data,
        total_comptes=total_comptes,
        total_ecarts=total_ecarts
    )

@app.route('/stock/inventory/history', methods=['GET'])
def inventory_history():
    """View for the inventory history."""
    inventories = Inventory.query.filter_by(status='Complete').all()

    inventory_data = []
    for inventory in inventories:
        items = InventoryItems.query.filter_by(inventory_id=inventory.id).all()
        discrepancies = sum(1 for item in items if item.actual_quantity < item.recorded_quantity)
        inventory_data.append({
            'inventory': inventory,
            'total_articles': len(items),
            'discrepancies': discrepancies,
        })

    return render_template('stock/inventory_history.html', inventory_data=inventory_data)

@app.route('/suppliers')
def suppliers():
    suppliers = Suppliers.query.all()
    return render_template('suppliers/list.html', suppliers=suppliers)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()
