import os
import django
import sys
import re
from django.utils.text import slugify
from decimal import Decimal

# Set up Django environment
sys.path.append('cleaningservices')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cleaningservices.settings')
django.setup()

from shop.models import Product, ProductCategory, AffiliatePartner

# Define product data with affiliate links
products = [
    {
        'title': 'Vileda UltraMat Turbo Komplettset, Bodenwischer mit Eimer und Powerschleuder',
        'description': '''
Der Vileda UltraMat Turbo ist ein hochwertiges Wischmopp-Set mit einem innovativen Schleudermechanismus für müheloses und effizientes Reinigen aller Hartböden.

Eigenschaften:
- PowerSchleuder mit Pedal-Mechanismus für kraftvolles Auswringen ohne Bücken
- Optimale Bodenreinigung mit minimaler Kraftanstrengung
- Passt für alle Bodenwischer Bezüge von Vileda
- Einfaches Befestigen und Wechseln des Bezugs dank praktischem Klicksystem
- Extra breiter 34cm Mikrofaserbezug für schnelleres Wischen großer Flächen
        ''',
        'price': Decimal('49.99'),
        'amazon_url': 'https://amzn.to/42Cd05m',
        'features': [
            'Kraftvolle Schleuderwirkung durch Pedal-Mechanismus',
            'Ergonomischer Teleskopstiel für bequemes Wischen',
            'Hochwertige Mikrofasern für optimale Schmutzaufnahme',
            'Für alle Hartböden geeignet',
            'Inklusive Wischbezug und Eimer mit Spritzschutz'
        ],
        'rating': Decimal('4.5')
    },
    {
        'title': 'SUPER CLEAN Reinigungsknete Auto - 100g Magic Clean Knete',
        'description': '''
Die SUPER CLEAN Reinigungsknete entfernt mühelos industriellen Fallout, Baumharz, Teerflecken und eingebrannten Bremsstaub von Ihrem Fahrzeug ohne die Oberfläche zu beschädigen.

Die professionelle Reinigungsknete für Ihr Auto:
- Einfache Anwendung: Die Knete gleitet sanft über die Oberfläche und nimmt Schmutzpartikel auf
- Für alle glatten Oberflächen: Autolack, Fenster, Felgen und mehr
- Wiederverwendbar und langlebig
- Ideal zur Vorbereitung vor einer Politur oder Versiegelung
        ''',
        'price': Decimal('9.99'),
        'amazon_url': 'https://amzn.to/3R6Zxfz',
        'features': [
            'Entfernt hartnäckige Verschmutzungen ohne Kratzer',
            'Macht die Oberfläche glatt wie Glas',
            'Vielseitig einsetzbar für Auto, Boot, Motorrad',
            '100g Premium Qualität',
            'Made in Germany'
        ],
        'rating': Decimal('4.2')
    },
    {
        'title': 'Kärcher Fenstersauger WV 2 Plus N (Akkulaufzeit: 35 min, 2x wechselbare Absaugdüsen)',
        'description': '''
Der Kärcher Fenstersauger WV 2 Plus N saugt Reinigungswasser streifenfrei von glatten Oberflächen ab und macht Schluss mit mühseligem Wischen und Trocknen.

Produktdetails:
- Akkulaufzeit bis zu 35 Minuten - für bis zu 105 m² Reinigungsfläche
- Streifenfreies Sauberwerden von allen glatten Oberflächen wie Fenstern, Fliesen, Spiegel und Duschkabinen
- Leicht und handlich (nur 600 g) - für komfortables Arbeiten
- Mit praktischer LED-Anzeige zur Ladezustandskontrolle
- Inklusive 2 unterschiedlich großer Absaugdüsen und Sprühflasche mit Mikrofaserbezug
        ''',
        'price': Decimal('67.99'),
        'sale_price': Decimal('59.99'),
        'amazon_url': 'https://amzn.to/444Vvft',
        'features': [
            'Leistungsstarker Lithium-Ionen-Akku mit 35 Minuten Laufzeit',
            'Streifenfreie Reinigung durch präzise Absaugung',
            'Zwei Absaugdüsen (170 mm und 280 mm) für unterschiedliche Einsatzbereiche',
            'Inklusive Sprühflasche mit Mikrofaserbezug',
            'Kompaktes Design mit nur 600g Gewicht'
        ],
        'rating': Decimal('4.7')
    },
    {
        'title': 'MR.SIGA Mikrofaser-Reinigungstücher, 12er-Pack',
        'description': '''
Die MR.SIGA Mikrofaser-Reinigungstücher sind vielseitige Helfer für zahlreiche Reinigungsaufgaben im Haushalt. Dank der hochwertigen Mikrofasern nehmen sie Staub, Schmutz und Feuchtigkeit effektiv auf.

Produktvorteile:
- Ausgezeichnete Saugfähigkeit und Reinigungsleistung
- Weich und schonend für alle Oberflächen
- Langlebig und wiederverwendbar
- Fusselfrei für streifenfreie Ergebnisse
- Maschinenwaschbar bei bis zu 60°C
        ''',
        'price': Decimal('14.99'),
        'amazon_url': 'https://amzn.to/43NM4Rq',
        'features': [
            '12 Tücher im praktischen Set (30 x 30 cm)',
            'Ultra-Mikrofasern mit 220.000 Fasern pro Quadratzoll',
            'Für trockene und nasse Anwendungen geeignet',
            'Reinigt mit oder ohne Reinigungsmittel',
            'Verschiedene Farben für unterschiedliche Bereiche'
        ],
        'rating': Decimal('4.6')
    },
    {
        'title': 'Kärcher Hochdruckreiniger K 5 Premium Smart Control',
        'description': '''
Der Kärcher K 5 Premium Smart Control Hochdruckreiniger mit Bluetooth-Verbindung und App-Unterstützung für optimale Reinigungsergebnisse bei mittlerem Verschmutzungsgrad.

Features:
- Smart Control: Einfache Bedienung über die Home & Garden App mit praktischen Anwendungshilfen
- Hocheffizienter Wasser-gekühlter Motor für lange Lebensdauer und hohe Leistung
- Plug 'n' Clean System für einfachen Reinigungsmittelwechsel
- 3-in-1 Multi Jet Strahlrohr mit Flach-, Rund- und Reinigungsmittelstrahl
- Integrierte Schlauchtrommel für ordentliche Aufbewahrung des 10m Hochdruckschlauchs
        ''',
        'price': Decimal('449.99'),
        'sale_price': Decimal('399.99'),
        'amazon_url': 'https://amzn.to/4ljXfHT',
        'features': [
            'Leistungsstarker 2100 Watt Motor',
            'Druck bis zu 145 bar',
            'Wasserfördermenge bis zu 500 l/h',
            'Smart Control mit App-Steuerung',
            'Inklusive umfangreichem Zubehör'
        ],
        'rating': Decimal('4.8')
    },
]

def extract_asin(url):
    """Extract ASIN from Amazon URL."""
    # Try to extract from bitly URL
    matches = re.search(r'amzn\.to/([A-Za-z0-9]+)', url)
    if matches:
        return matches.group(1)
    
    # Try to extract from regular amazon url
    matches = re.search(r'amazon\.[a-z]+/[^/]+/([A-Z0-9]{10})', url)
    if matches:
        return matches.group(1)
    
    return None

# Find the required models
category = ProductCategory.objects.get(name='Cleaning Supplies')
partner = AffiliatePartner.objects.get(name='Amazon DE')

# Add products
for product_data in products:
    # Generate slug from title
    slug = slugify(product_data['title'])
    
    # Get ASIN from URL if possible
    asin = extract_asin(product_data['amazon_url'])
    
    # Check if product already exists to avoid duplicates
    if not Product.objects.filter(slug=slug).exists():
        product = Product(
            title=product_data['title'],
            slug=slug,
            category=category,
            description=product_data['description'],
            features=product_data['features'],
            price=product_data['price'],
            amazon_asin=asin,
            amazon_url=product_data['amazon_url'],
            affiliate_tag=partner.affiliate_id,
            rating=product_data['rating'],
            # We don't have image files, so we'll use placeholders
            image_main='shop/products/placeholder.svg'
        )
        
        # Add sale price if available
        if 'sale_price' in product_data:
            product.sale_price = product_data['sale_price']
            
        product.save()
        print(f"Added product: {product.title}")
    else:
        print(f"Product already exists: {product_data['title']}")

print("Finished adding products!")