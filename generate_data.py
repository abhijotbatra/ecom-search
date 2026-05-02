"""
Run this once to generate sample_products.xlsx
  python data/generate_data.py
"""
import pandas as pd
import os

products = [
    # Electronics - Headphones
    {"id":"P001","name":"Sony WH-1000XM5 Wireless Headphones","category":"Electronics","subcategory":"Headphones","brand":"Sony","price":29990,"rating":4.8,"stock":45,"description":"Industry-leading noise cancelling wireless headphones with 30hr battery, multipoint connection, crystal clear hands-free calling. Perfect for travel and work from home.","tags":"noise cancelling wireless bluetooth premium travel"},
    {"id":"P002","name":"boAt Rockerz 450 Bluetooth Headphone","category":"Electronics","subcategory":"Headphones","brand":"boAt","price":1499,"rating":4.2,"stock":200,"description":"On-ear wireless headphone with 15hr battery, 40mm drivers, and deep bass. Ideal for casual listening and calls.","tags":"wireless bluetooth bass budget casual"},
    {"id":"P003","name":"JBL Tune 760NC Noise Cancelling","category":"Electronics","subcategory":"Headphones","brand":"JBL","price":5999,"rating":4.5,"stock":80,"description":"Active noise cancellation with 35hr playtime, JBL Pure Bass sound. Foldable design for easy travel.","tags":"noise cancelling jbl bass foldable travel wireless"},
    {"id":"P004","name":"Sennheiser HD 450BT Wireless","category":"Electronics","subcategory":"Headphones","brand":"Sennheiser","price":7990,"rating":4.6,"stock":35,"description":"Premium over-ear headphone with active noise cancellation, 30hr battery, and audiophile-grade sound quality.","tags":"premium audiophile noise cancelling wireless sennheiser"},
    {"id":"P005","name":"Realme Buds Wireless 2 Neo","category":"Electronics","subcategory":"Earphones","brand":"Realme","price":999,"rating":4.0,"stock":300,"description":"Budget neckband earphone with magnetic clasp, 17hr battery, IPX4 water resistance.","tags":"budget neckband earphone wireless ipx4 realme"},

    # Electronics - Gaming
    {"id":"P006","name":"Razer BlackShark V2 Gaming Headset","category":"Electronics","subcategory":"Gaming","brand":"Razer","price":8999,"rating":4.7,"stock":60,"description":"Professional gaming headset with THX Spatial Audio, cardioid mic, 7.1 surround sound. Built for competitive gaming and streaming.","tags":"gaming headset rgb razer surround sound mic esports"},
    {"id":"P007","name":"HyperX Cloud Stinger Core Gaming","category":"Electronics","subcategory":"Gaming","brand":"HyperX","price":4999,"rating":4.4,"stock":90,"description":"Lightweight gaming headset with 7.1 surround sound, noise-cancelling mic, memory foam ear cushions.","tags":"gaming headset lightweight surround hyperx comfortable"},
    {"id":"P008","name":"Logitech G502 HERO Gaming Mouse","category":"Electronics","subcategory":"Gaming","brand":"Logitech","price":4995,"rating":4.8,"stock":120,"description":"High performance gaming mouse with HERO 25K sensor, 11 programmable buttons, RGB lighting, adjustable weights.","tags":"gaming mouse rgb logitech programmable sensor precise"},
    {"id":"P009","name":"Corsair K70 RGB Mechanical Keyboard","category":"Electronics","subcategory":"Gaming","brand":"Corsair","price":13999,"rating":4.7,"stock":40,"description":"Full mechanical gaming keyboard with Cherry MX switches, per-key RGB backlighting, aluminum frame, dedicated media keys.","tags":"mechanical keyboard rgb gaming corsair cherry mx aluminum"},
    {"id":"P010","name":"SteelSeries Arctis 7P+ Wireless","category":"Electronics","subcategory":"Gaming","brand":"SteelSeries","price":14999,"rating":4.6,"stock":25,"description":"Lossless 2.4GHz wireless gaming headset, 30hr battery, Discord-certified ClearCast mic, works on PS5 PC Switch.","tags":"gaming headset wireless steelseries ps5 discord mic"},

    # Electronics - Laptops
    {"id":"P011","name":"ASUS VivoBook 15 Core i5","category":"Electronics","subcategory":"Laptops","brand":"ASUS","price":54990,"rating":4.3,"stock":30,"description":"15.6-inch FHD laptop with Intel Core i5-12th Gen, 16GB RAM, 512GB SSD, Windows 11. Great for students and professionals.","tags":"laptop student professional asus i5 ssd windows"},
    {"id":"P012","name":"Lenovo IdeaPad Slim 3 Ryzen 5","category":"Electronics","subcategory":"Laptops","brand":"Lenovo","price":42990,"rating":4.2,"stock":55,"description":"Thin and light laptop with AMD Ryzen 5, 8GB RAM, 512GB SSD, 15.6-inch display. Budget-friendly for everyday use.","tags":"laptop budget thin light lenovo ryzen everyday"},
    {"id":"P013","name":"MacBook Air M2 13-inch","category":"Electronics","subcategory":"Laptops","brand":"Apple","price":114900,"rating":4.9,"stock":20,"description":"Apple M2 chip, 8GB unified memory, 256GB SSD, 18hr battery, fanless design, Liquid Retina display. Premium laptop.","tags":"apple macbook premium m2 fanless retina battery"},
    {"id":"P014","name":"HP Pavilion Gaming Laptop","category":"Electronics","subcategory":"Laptops","brand":"HP","price":67990,"rating":4.4,"stock":18,"description":"Gaming laptop with RTX 3050, Intel i5-12th Gen, 16GB RAM, 512GB SSD, 144Hz display. Entry gaming performance.","tags":"gaming laptop rtx hp entry level 144hz display"},

    # Electronics - Monitors
    {"id":"P015","name":"LG 27-inch 4K IPS Monitor","category":"Electronics","subcategory":"Monitors","brand":"LG","price":28990,"rating":4.6,"stock":22,"description":"27-inch 4K UHD IPS display, 60Hz, HDR10, USB-C, HDMI, DisplayPort. Stunning colour accuracy for design and content work.","tags":"monitor 4k ips design colour accurate usbc lg"},
    {"id":"P016","name":"Samsung 24-inch FHD Monitor","category":"Electronics","subcategory":"Monitors","brand":"Samsung","price":11990,"rating":4.3,"stock":75,"description":"24-inch Full HD IPS monitor, 75Hz, AMD FreeSync, eye comfort mode. Budget display for home and office use.","tags":"monitor budget office freesync samsung 75hz"},
    {"id":"P017","name":"ASUS TUF Gaming 27-inch 165Hz","category":"Electronics","subcategory":"Monitors","brand":"ASUS","price":22990,"rating":4.7,"stock":30,"description":"27-inch 1440p QHD gaming monitor, 165Hz, 1ms response, G-Sync compatible, HDR, IPS panel. Excellent for competitive gaming.","tags":"gaming monitor 165hz 1440p gsync asus competitive"},

    # Electronics - Phones
    {"id":"P018","name":"Samsung Galaxy S23 Ultra","category":"Electronics","subcategory":"Smartphones","brand":"Samsung","price":124999,"rating":4.8,"stock":15,"description":"200MP camera, S-Pen, Snapdragon 8 Gen 2, 5000mAh battery, 12GB RAM. The ultimate Android flagship.","tags":"samsung flagship android camera spen 200mp 5g premium"},
    {"id":"P019","name":"Redmi Note 12 Pro 5G","category":"Electronics","subcategory":"Smartphones","brand":"Redmi","price":22999,"rating":4.4,"stock":150,"description":"50MP camera, 5G, Dimensity 1080, 120Hz AMOLED display, 5000mAh battery. Best value mid-range phone.","tags":"5g midrange redmi camera amoled 120hz value"},
    {"id":"P020","name":"iPhone 15 128GB","category":"Electronics","subcategory":"Smartphones","brand":"Apple","price":79900,"rating":4.7,"stock":40,"description":"A16 Bionic chip, 48MP camera system, Dynamic Island, USB-C, ceramic shield, all-day battery. iOS ecosystem.","tags":"iphone apple ios premium camera dynamic island usbc"},

    # Home & Kitchen
    {"id":"P021","name":"Prestige Iris 750W Mixer Grinder","category":"Home & Kitchen","subcategory":"Appliances","brand":"Prestige","price":2999,"rating":4.3,"stock":100,"description":"750W mixer grinder with 3 stainless steel jars, 3 speed control, whipper attachment. Ideal for Indian cooking.","tags":"mixer grinder kitchen prestige indian cooking stainless"},
    {"id":"P022","name":"Philips Air Fryer HD9252","category":"Home & Kitchen","subcategory":"Appliances","brand":"Philips","price":9499,"rating":4.5,"stock":60,"description":"4.1L air fryer with Rapid Air technology, 80% less fat, 7 pre-set programs, dishwasher-safe parts.","tags":"air fryer healthy cooking philips low fat kitchen"},
    {"id":"P023","name":"Kent Grand Plus Water Purifier","category":"Home & Kitchen","subcategory":"Appliances","brand":"Kent","price":16500,"rating":4.4,"stock":35,"description":"RO+UV+UF+TDS purification, 9L storage, 20L/hr purification rate, mineral retention. Ideal for Indian homes.","tags":"water purifier ro uv kent mineral healthy home"},
    {"id":"P024","name":"Bajaj Majesty 1000W Room Heater","category":"Home & Kitchen","subcategory":"Appliances","brand":"Bajaj","price":1699,"rating":4.1,"stock":80,"description":"1000W fan room heater with overheat protection, adjustable thermostat, instant heat. Suitable for small rooms.","tags":"room heater winter bajaj thermostat instant heat"},
    {"id":"P025","name":"Wonderchef Nutri-Blend 400W","category":"Electronics","subcategory":"Appliances","brand":"Wonderchef","price":2199,"rating":4.2,"stock":90,"description":"Personal blender for smoothies, protein shakes, with 2 jars, stainless blades, portable and compact.","tags":"blender smoothie protein personal compact portable"},

    # Study & Productivity
    {"id":"P026","name":"Kindle Paperwhite 16GB","category":"Electronics","subcategory":"E-readers","brand":"Amazon","price":14999,"rating":4.7,"stock":55,"description":"6.8-inch 300ppi glare-free display, adjustable warm light, 10-week battery, waterproof, 16GB storage. Read anywhere.","tags":"ebook kindle reading study waterproof glare free"},
    {"id":"P027","name":"Wacom Intuos Small Drawing Tablet","category":"Electronics","subcategory":"Accessories","brand":"Wacom","price":5990,"rating":4.5,"stock":40,"description":"USB graphics tablet for digital art, photo editing, note-taking. 4096 pressure levels, compatible with Mac and Windows.","tags":"drawing tablet wacom digital art design sketch note"},
    {"id":"P028","name":"Casio FX-991EX Scientific Calculator","category":"Stationery","subcategory":"Calculators","brand":"Casio","price":1295,"rating":4.8,"stock":200,"description":"Advanced scientific calculator with 552 functions, spreadsheet, QR code, natural textbook display. For engineering and science.","tags":"calculator scientific casio engineering exam maths"},
    {"id":"P029","name":"Uniball One Gel Pen Set 12pcs","category":"Stationery","subcategory":"Pens","brand":"Uniball","price":840,"rating":4.6,"stock":300,"description":"Smooth gel writing pens in 12 colours, 0.38mm tip, archival ink, smear-free, great for notes and journaling.","tags":"pen gel writing notes journaling colour smooth"},
    {"id":"P030","name":"Moleskine Classic Hard Cover Notebook","category":"Stationery","subcategory":"Notebooks","brand":"Moleskine","price":1299,"rating":4.5,"stock":150,"description":"A5 ruled notebook, 240 pages, hard cover, elastic closure, expandable pocket. Iconic notebook for professionals.","tags":"notebook journal writing professional ruled moleskine"},

    # Fitness
    {"id":"P031","name":"Fitbit Charge 5 Fitness Tracker","category":"Fitness","subcategory":"Wearables","brand":"Fitbit","price":14999,"rating":4.5,"stock":30,"description":"Advanced fitness tracker with built-in GPS, heart rate, SpO2, stress management score, 7-day battery, sleep tracking.","tags":"fitness tracker fitbit gps heart rate sleep health"},
    {"id":"P032","name":"Boldfit Resistance Bands Set","category":"Fitness","subcategory":"Equipment","brand":"Boldfit","price":599,"rating":4.3,"stock":500,"description":"Set of 5 resistance bands, 5 resistance levels, anti-snap latex, for home workouts, yoga, stretching, physio.","tags":"resistance bands workout home gym yoga fitness beginner"},
    {"id":"P033","name":"Skullcandy Push Active True Wireless","category":"Electronics","subcategory":"Earphones","brand":"Skullcandy","price":3999,"rating":4.2,"stock":70,"description":"IPX7 waterproof true wireless earbuds, 35hr battery with case, secure fit for running and workouts.","tags":"earphones workout running waterproof ipx7 wireless gym sport"},
    {"id":"P034","name":"Strauss Yoga Mat 6mm","category":"Fitness","subcategory":"Equipment","brand":"Strauss","price":799,"rating":4.4,"stock":200,"description":"6mm thick anti-slip yoga mat, TPE material, eco-friendly, carrying strap, 183x61cm. Good for yoga and pilates.","tags":"yoga mat exercise pilates eco friendly non slip fitness"},
    {"id":"P035","name":"Garmin Forerunner 55 GPS Watch","category":"Fitness","subcategory":"Wearables","brand":"Garmin","price":19990,"rating":4.6,"stock":20,"description":"GPS running watch with heart rate, VO2 max, training plans, 20hr GPS battery. Designed for runners.","tags":"gps watch running garmin heart rate vo2 training"},

    # Bags & Accessories
    {"id":"P036","name":"Wildcraft Laptop Backpack 35L","category":"Bags","subcategory":"Backpacks","brand":"Wildcraft","price":2199,"rating":4.3,"stock":80,"description":"35L laptop backpack, padded 15.6-inch laptop compartment, rain cover, ergonomic back, USB charging port.","tags":"backpack laptop travel wildcraft usb charging rain cover"},
    {"id":"P037","name":"Samsonite Volant Spinner 55cm","category":"Bags","subcategory":"Luggage","brand":"Samsonite","price":8499,"rating":4.5,"stock":25,"description":"Cabin-sized spinner trolley, TSA lock, 4 spinner wheels, 55cm. Lightweight and durable for frequent flyers.","tags":"luggage trolley travel samsonite tsa cabin carry on"},
    {"id":"P038","name":"Urban Monkey Crossbody Sling Bag","category":"Bags","subcategory":"Sling Bags","brand":"Urban Monkey","price":1299,"rating":4.2,"stock":120,"description":"Compact crossbody bag, water-resistant, multiple pockets, adjustable strap. Good for daily commute and travel.","tags":"sling bag crossbody daily travel compact water resistant"},

    # Lighting & Study Setup
    {"id":"P039","name":"Philips LED Desk Lamp 8W","category":"Home & Kitchen","subcategory":"Lighting","brand":"Philips","price":1299,"rating":4.4,"stock":100,"description":"8W LED desk lamp, adjustable brightness, 4 colour modes, USB charging port, eye protection, touch control.","tags":"desk lamp study led eye care philips touch usb"},
    {"id":"P040","name":"Portronics Toad 25 LED Desk Lamp","category":"Home & Kitchen","subcategory":"Lighting","brand":"Portronics","price":899,"rating":4.1,"stock":150,"description":"USB-powered LED desk lamp, 10 brightness levels, flexible neck, eye-friendly light for study and late night work.","tags":"desk lamp study led usb flexible brightness night"},

    # Cameras
    {"id":"P041","name":"GoPro Hero 12 Black Action Camera","category":"Electronics","subcategory":"Cameras","brand":"GoPro","price":44990,"rating":4.7,"stock":18,"description":"4K 120fps action camera, HyperSmooth 6.0 stabilisation, waterproof to 10m, HDR video, voice control.","tags":"action camera gopro 4k waterproof travel adventure vlog"},
    {"id":"P042","name":"Canon EOS M50 Mark II Mirrorless","category":"Electronics","subcategory":"Cameras","brand":"Canon","price":54990,"rating":4.6,"stock":12,"description":"24.1MP mirrorless camera with Dual Pixel AF, 4K video, flippy touchscreen, eye tracking. Great for vloggers and beginners.","tags":"mirrorless camera canon vlog youtube beginner 4k autofocus"},

    # Chairs & Furniture
    {"id":"P043","name":"Green Soul Monster Ultimate Gaming Chair","category":"Furniture","subcategory":"Chairs","brand":"Green Soul","price":18990,"rating":4.4,"stock":10,"description":"Ergonomic gaming and office chair, adjustable lumbar support, 4D armrests, recline to 180°, cold foam cushion.","tags":"gaming chair ergonomic lumbar office work from home recline"},
    {"id":"P044","name":"Wakefit Orthopaedic Memory Foam Chair","category":"Furniture","subcategory":"Chairs","brand":"Wakefit","price":12990,"rating":4.5,"stock":15,"description":"High-back ergonomic office chair with memory foam seat, adjustable headrest, lumbar support, breathable mesh back.","tags":"office chair ergonomic memory foam work from home lumbar mesh"},

    # Cables & Power
    {"id":"P045","name":"Anker 65W GaN USB-C Charger","category":"Electronics","subcategory":"Chargers","brand":"Anker","price":3499,"rating":4.7,"stock":90,"description":"65W GaN fast charger, 2 USB-C + 1 USB-A, compact design, supports MacBook, laptops, phones. Travel-friendly.","tags":"gan charger fast charging usbc anker laptop macbook compact"},
    {"id":"P046","name":"Belkin 10000mAh Power Bank","category":"Electronics","subcategory":"Power Banks","brand":"Belkin","price":2999,"rating":4.3,"stock":70,"description":"10000mAh slim power bank, 15W fast charge, USB-C in/out, USB-A, LED indicator, pocket-sized.","tags":"power bank portable charger belkin fast charge usbc travel"},

    # Smart Home
    {"id":"P047","name":"Amazon Echo Dot 5th Gen","category":"Electronics","subcategory":"Smart Home","brand":"Amazon","price":4999,"rating":4.5,"stock":60,"description":"Smart speaker with Alexa, improved bass, motion detection, temperature sensor, connect smart home devices.","tags":"smart speaker alexa amazon echo smart home voice control"},
    {"id":"P048","name":"TP-Link Tapo Smart Bulb L530","category":"Electronics","subcategory":"Smart Home","brand":"TP-Link","price":999,"rating":4.4,"stock":200,"description":"16M colour smart WiFi bulb, works with Alexa and Google Home, schedule, dim, no hub required.","tags":"smart bulb wifi alexa google home colour dimmer schedule"},

    # Cables
    {"id":"P049","name":"Anker USB-C to USB-C Cable 1.8m","category":"Electronics","subcategory":"Cables","brand":"Anker","price":799,"rating":4.6,"stock":300,"description":"100W USB-C to USB-C braided nylon cable, 1.8m, supports fast charging and data transfer up to 480Mbps.","tags":"cable usbc fast charge data transfer braided anker"},
    {"id":"P050","name":"AmazonBasics HDMI Cable 2m","category":"Electronics","subcategory":"Cables","brand":"AmazonBasics","price":449,"rating":4.2,"stock":400,"description":"2m HDMI 2.0 cable, supports 4K 60Hz, HDR, ARC. Compatible with TV, monitor, laptop, gaming consoles.","tags":"hdmi cable 4k tv monitor laptop gaming console"},
]

df = pd.DataFrame(products)
os.makedirs("data", exist_ok=True)
output_path = os.path.join(os.path.dirname(__file__), "sample_products.xlsx")
df.to_excel(output_path, index=False)
print(f"Generated {len(df)} products → {output_path}")
print(df[["id","name","price","rating"]].to_string())
