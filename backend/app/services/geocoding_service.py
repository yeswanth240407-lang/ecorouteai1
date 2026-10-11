import httpx
import logging
from typing import Optional, Dict, Any, List, Tuple
from app.models.schemas import Stop

logger = logging.getLogger(__name__)

# Pre-indexed Indian States & Major Logistics Corridors
INDIAN_HUBS_DB: Dict[str, Dict[str, Any]] = {
    "chennai": {
        "city_name": "Chennai (Madras)",
        "state": "Tamil Nadu",
        "depot": {"name": "Ennore Port & Ponneri Logistics Hub", "lat": 13.3493, "lng": 80.2497},
        "stops": [
            {"name": "Ponneri Industrial Smart City", "lat": 13.3323, "lng": 80.1983, "demand": 160.0},
            {"name": "Sriperumbudur Auto Cluster Hub", "lat": 12.9675, "lng": 79.9441, "demand": 190.0},
            {"name": "Ambattur Industrial Estate", "lat": 13.0983, "lng": 80.1623, "demand": 130.0},
            {"name": "Guindy Industrial Estate & IT Park", "lat": 13.0067, "lng": 80.2025, "demand": 110.0},
            {"name": "OMR Sholinganallur Tech Corridor", "lat": 12.9010, "lng": 80.2279, "demand": 140.0},
            {"name": "Tiruvallur Rail Freight Terminal", "lat": 13.1436, "lng": 79.9079, "demand": 120.0},
        ]
    },
    "bengaluru": {
        "city_name": "Bengaluru (Bangalore)",
        "state": "Karnataka",
        "depot": {"name": "Peenya Industrial Logistics Hub", "lat": 13.0285, "lng": 77.5197},
        "stops": [
            {"name": "Koramangala 4th Block Hub", "lat": 12.9352, "lng": 77.6245, "demand": 140.0},
            {"name": "Indiranagar 100ft Road Retail", "lat": 12.9784, "lng": 77.6408, "demand": 95.0},
            {"name": "Whitefield ITPL Tech Corridor", "lat": 12.9698, "lng": 77.7499, "demand": 180.0},
            {"name": "Electronic City Phase 1 Express", "lat": 12.8452, "lng": 77.6602, "demand": 120.0},
            {"name": "MG Road Central Commercial", "lat": 12.9756, "lng": 77.6066, "demand": 80.0},
            {"name": "Malleshwaram Retail Market", "lat": 13.0031, "lng": 77.5704, "demand": 110.0},
        ]
    },
    "mumbai": {
        "city_name": "Mumbai MMR",
        "state": "Maharashtra",
        "depot": {"name": "Bhiwandi Integrated Warehousing Hub", "lat": 19.2967, "lng": 73.0631},
        "stops": [
            {"name": "Bandra Kurla Complex (BKC)", "lat": 19.0657, "lng": 72.8687, "demand": 175.0},
            {"name": "Andheri East MIDC Commercial", "lat": 19.1197, "lng": 72.8664, "demand": 140.0},
            {"name": "Nariman Point Business District", "lat": 18.9256, "lng": 72.8242, "demand": 110.0},
            {"name": "Powai Hiranandani Tech Hub", "lat": 19.1176, "lng": 72.9060, "demand": 95.0},
            {"name": "Thane West Retail Zone", "lat": 19.2183, "lng": 72.9781, "demand": 130.0},
            {"name": "JNPT Port Container Logistics", "lat": 18.9499, "lng": 72.9515, "demand": 210.0},
        ]
    },
    "delhi": {
        "city_name": "Delhi NCR",
        "state": "National Capital Region",
        "depot": {"name": "Okhla Phase III Logistics Center", "lat": 28.5355, "lng": 77.2685},
        "stops": [
            {"name": "Connaught Place Central Hub", "lat": 28.6315, "lng": 77.2167, "demand": 150.0},
            {"name": "Gurgaon DLF Cyber City", "lat": 28.4950, "lng": 77.0895, "demand": 210.0},
            {"name": "Noida Sector 62 IT Park", "lat": 28.6280, "lng": 77.3649, "demand": 130.0},
            {"name": "Nehru Place Electronics Market", "lat": 28.5494, "lng": 77.2528, "demand": 90.0},
            {"name": "Aerocity Cargo Terminal", "lat": 28.5524, "lng": 77.1216, "demand": 160.0},
        ]
    },
    "hyderabad": {
        "city_name": "Hyderabad",
        "state": "Telangana",
        "depot": {"name": "Shamshabad Airport Logistics Park", "lat": 17.2403, "lng": 78.4294},
        "stops": [
            {"name": "Hitec City Cyber Towers", "lat": 17.4504, "lng": 78.3808, "demand": 160.0},
            {"name": "Gachibowli Financial District", "lat": 17.4401, "lng": 78.3489, "demand": 130.0},
            {"name": "Banjara Hills Commercial", "lat": 17.4156, "lng": 78.4350, "demand": 100.0},
            {"name": "Secunderabad Railway Goods Yard", "lat": 17.4399, "lng": 78.4983, "demand": 180.0},
            {"name": "Madhapur Retail Strip", "lat": 17.4483, "lng": 78.3915, "demand": 90.0},
        ]
    },
    "kolkata": {
        "city_name": "Kolkata (Calcutta)",
        "state": "West Bengal",
        "depot": {"name": "Dankuni Multi-Modal Logistics Hub", "lat": 22.6845, "lng": 88.2917},
        "stops": [
            {"name": "Salt Lake Sector V IT Hub", "lat": 22.5802, "lng": 88.4344, "demand": 150.0},
            {"name": "Park Street Commercial Centre", "lat": 22.5535, "lng": 88.3533, "demand": 120.0},
            {"name": "New Town Ecospace Tech Park", "lat": 22.5855, "lng": 88.4727, "demand": 140.0},
            {"name": "Howrah Freight Terminal", "lat": 22.5850, "lng": 88.3468, "demand": 190.0},
            {"name": "Burrabazar Wholesale Trading", "lat": 22.5866, "lng": 88.3547, "demand": 160.0},
        ]
    },
    "pune": {
        "city_name": "Pune",
        "state": "Maharashtra",
        "depot": {"name": "Chakan Auto & Industrial Hub", "lat": 18.7583, "lng": 73.8583},
        "stops": [
            {"name": "Hinjawadi Rajiv Gandhi Infotech Park", "lat": 18.5913, "lng": 73.7389, "demand": 180.0},
            {"name": "Bhosari MIDC Logistics Strip", "lat": 18.6344, "lng": 73.8444, "demand": 140.0},
            {"name": "Kharadi EON Free Zone", "lat": 18.5515, "lng": 73.9493, "demand": 130.0},
            {"name": "Shivajinagar Commercial Center", "lat": 18.5308, "lng": 73.8475, "demand": 100.0},
            {"name": "Magarpatta Cybercity", "lat": 18.5134, "lng": 73.9298, "demand": 120.0},
        ]
    },
    "ahmedabad": {
        "city_name": "Ahmedabad",
        "state": "Gujarat",
        "depot": {"name": "Sanand Industrial Logistics Hub", "lat": 22.9868, "lng": 72.3813},
        "stops": [
            {"name": "GIFT City Financial Zone", "lat": 23.1611, "lng": 72.6844, "demand": 160.0},
            {"name": "SG Highway Commercial Corridor", "lat": 23.0338, "lng": 72.5074, "demand": 130.0},
            {"name": "Changodar Industrial Area", "lat": 22.9238, "lng": 72.4431, "demand": 150.0},
            {"name": "Naroda Industrial Estate", "lat": 23.0728, "lng": 72.6599, "demand": 140.0},
            {"name": "Prahlad Nagar Corporate Hub", "lat": 23.0125, "lng": 72.5085, "demand": 110.0},
        ]
    },
    "kochi": {
        "city_name": "Kochi (Cochin)",
        "state": "Kerala",
        "depot": {"name": "Vallarpadam Container Terminal & Port", "lat": 9.9839, "lng": 76.2428},
        "stops": [
            {"name": "Infopark Kakkanad IT Express", "lat": 10.0120, "lng": 76.3639, "demand": 140.0},
            {"name": "MG Road Retail Hub Ernakulam", "lat": 9.9723, "lng": 76.2844, "demand": 100.0},
            {"name": "Kalamassery Industrial Estate", "lat": 10.0543, "lng": 76.3218, "demand": 130.0},
            {"name": "Willingdon Island Freight Zone", "lat": 9.9482, "lng": 76.2736, "demand": 170.0},
            {"name": "Aluva Logistics Strip", "lat": 10.1076, "lng": 76.3516, "demand": 120.0},
        ]
    },
    "jaipur": {
        "city_name": "Jaipur (Pink City)",
        "state": "Rajasthan",
        "depot": {"name": "VKI Industrial Area Sikar Road", "lat": 26.9744, "lng": 75.7686},
        "stops": [
            {"name": "Sitapura Industrial Area", "lat": 26.7766, "lng": 75.8344, "demand": 160.0},
            {"name": "Malviya Nagar Commercial", "lat": 26.8530, "lng": 75.8052, "demand": 120.0},
            {"name": "Mansarovar Retail Market", "lat": 26.8628, "lng": 75.7601, "demand": 110.0},
            {"name": "C-Scheme Central Business Zone", "lat": 26.9115, "lng": 75.8016, "demand": 100.0},
            {"name": "Mahindra World City SEZ", "lat": 26.8569, "lng": 75.6022, "demand": 180.0},
        ]
    },
    "coimbatore": {
        "city_name": "Coimbatore",
        "state": "Tamil Nadu",
        "depot": {"name": "SIDCO Industrial Estate Kurichi", "lat": 10.9419, "lng": 76.9719},
        "stops": [
            {"name": "Tidel Park Coimbatore IT Hub", "lat": 11.0267, "lng": 77.0319, "demand": 150.0},
            {"name": "Peelamedu Tech & Textile Corridor", "lat": 11.0319, "lng": 77.0167, "demand": 130.0},
            {"name": "Gandhipuram Commercial Center", "lat": 11.0183, "lng": 76.9678, "demand": 110.0},
            {"name": "Singanallur Freight Zone", "lat": 10.9997, "lng": 77.0264, "demand": 140.0},
            {"name": "Saravanampatti Tech Zone", "lat": 11.0808, "lng": 76.9961, "demand": 120.0},
        ]
    },
    "lucknow": {
        "city_name": "Lucknow",
        "state": "Uttar Pradesh",
        "depot": {"name": "Transport Nagar Freight Terminal", "lat": 26.7828, "lng": 80.8797},
        "stops": [
            {"name": "Hazratganj Central District", "lat": 26.8504, "lng": 80.9499, "demand": 120.0},
            {"name": "Gomti Nagar IT City", "lat": 26.8646, "lng": 81.0142, "demand": 150.0},
            {"name": "Alambagh Commercial Hub", "lat": 26.8142, "lng": 80.9083, "demand": 110.0},
            {"name": "Chinhat Industrial Area", "lat": 26.8833, "lng": 81.0500, "demand": 140.0},
            {"name": "Amausi Airport Cargo Complex", "lat": 26.7644, "lng": 80.8842, "demand": 160.0},
        ]
    },
    "chandigarh": {
        "city_name": "Chandigarh Tricity",
        "state": "Punjab & Haryana",
        "depot": {"name": "Industrial Area Phase 1 Hub", "lat": 30.7046, "lng": 76.8041},
        "stops": [
            {"name": "Mohali Phase 8 IT City", "lat": 30.6975, "lng": 76.7175, "demand": 150.0},
            {"name": "Sector 17 Central Commercial Plaza", "lat": 30.7398, "lng": 76.7827, "demand": 110.0},
            {"name": "Panchkula Sector 14 Industrial Strip", "lat": 30.6922, "lng": 76.8542, "demand": 130.0},
            {"name": "Rajiv Gandhi Chandigarh Tech Park", "lat": 30.7244, "lng": 76.8408, "demand": 140.0},
            {"name": "Zirakpur Logistics Transit Corridor", "lat": 30.6425, "lng": 76.8173, "demand": 160.0},
        ]
    },
    "visakhapatnam": {
        "city_name": "Visakhapatnam (Vizag)",
        "state": "Andhra Pradesh",
        "depot": {"name": "Visakhapatnam Port & Container Terminal", "lat": 17.6908, "lng": 83.2922},
        "stops": [
            {"name": "Duvvada VSEZ Industrial Zone", "lat": 17.7083, "lng": 83.1500, "demand": 170.0},
            {"name": "Gajuwaka Industrial Corridor", "lat": 17.6958, "lng": 83.2114, "demand": 140.0},
            {"name": "Rushikonda IT SEZ", "lat": 17.7881, "lng": 83.3847, "demand": 130.0},
            {"name": "Siripuram Commercial Centre", "lat": 17.7225, "lng": 83.3150, "demand": 110.0},
            {"name": "Atchutapuram SEZ Freight Hub", "lat": 17.5458, "lng": 82.9917, "demand": 180.0},
        ]
    },
    "indore": {
        "city_name": "Indore",
        "state": "Madhya Pradesh",
        "depot": {"name": "Pithampur Auto & Pharma SEZ", "lat": 22.6144, "lng": 75.6881},
        "stops": [
            {"name": "Sanwer Road Industrial Area", "lat": 22.7667, "lng": 75.8500, "demand": 150.0},
            {"name": "Vijay Nagar Commercial Square", "lat": 22.7533, "lng": 75.8937, "demand": 120.0},
            {"name": "Crystal IT Park Ring Road", "lat": 22.6917, "lng": 75.8750, "demand": 130.0},
            {"name": "Rajwada Central Wholesale Market", "lat": 22.7186, "lng": 75.8550, "demand": 140.0},
            {"name": "Palasia Business Hub", "lat": 22.7244, "lng": 75.8839, "demand": 100.0},
        ]
    },
    "madurai": {
        "city_name": "Madurai",
        "state": "Tamil Nadu",
        "depot": {"name": "Madurai Ring Road Freight Terminal", "lat": 9.9252, "lng": 78.1198},
        "stops": [
            {"name": "Mattuthavani Integrated Terminal", "lat": 9.9482, "lng": 78.1565, "demand": 140.0},
            {"name": "Kappalur Industrial Estate SIDCO", "lat": 9.8450, "lng": 78.0310, "demand": 170.0},
            {"name": "Simmakkal Central Market", "lat": 9.9270, "lng": 78.1235, "demand": 120.0},
            {"name": "Thirunagar Logistics Zone", "lat": 9.8765, "lng": 78.0712, "demand": 110.0},
            {"name": "Vilangudi Industrial Area", "lat": 9.9610, "lng": 78.0980, "demand": 130.0},
        ]
    },
    "trichy": {
        "city_name": "Tiruchirappalli (Trichy)",
        "state": "Tamil Nadu",
        "depot": {"name": "Thuvakudi BHEL Logistics Hub", "lat": 10.7485, "lng": 78.7845},
        "stops": [
            {"name": "Tiruverumbur Heavy Industrial Corridor", "lat": 10.7675, "lng": 78.7565, "demand": 160.0},
            {"name": "Central Bus Stand Commercial Hub", "lat": 10.7960, "lng": 78.6850, "demand": 120.0},
            {"name": "Ariyamangalam Freight Warehouse", "lat": 10.8030, "lng": 78.7180, "demand": 140.0},
            {"name": "Thillai Nagar Business Strip", "lat": 10.8240, "lng": 78.6890, "demand": 110.0},
            {"name": "Srirangam Heritage Goods Depot", "lat": 10.8620, "lng": 78.6920, "demand": 130.0},
        ]
    },
    "surat": {
        "city_name": "Surat (Diamond & Textile Hub)",
        "state": "Gujarat",
        "depot": {"name": "Hazira Port & Industrial Freight Hub", "lat": 21.1180, "lng": 72.6350},
        "stops": [
            {"name": "Surat Diamond Bourse (DREAM City)", "lat": 21.0925, "lng": 72.7885, "demand": 180.0},
            {"name": "Pandesara GIDC Textile Cluster", "lat": 21.1520, "lng": 72.8250, "demand": 190.0},
            {"name": "Sachin Industrial Area GIDC", "lat": 21.0850, "lng": 72.8650, "demand": 150.0},
            {"name": "Ring Road Textile Wholesale Market", "lat": 21.1920, "lng": 72.8420, "demand": 130.0},
            {"name": "Adajan Commercial District", "lat": 21.1980, "lng": 72.7950, "demand": 110.0},
        ]
    },
    "bhopal": {
        "city_name": "Bhopal (City of Lakes)",
        "state": "Madhya Pradesh",
        "depot": {"name": "Mandideep Industrial Freight Corridor", "lat": 23.0845, "lng": 77.5185},
        "stops": [
            {"name": "Govindpura Industrial Area", "lat": 23.2560, "lng": 77.4520, "demand": 150.0},
            {"name": "MP Nagar Commercial Zone Zone-1", "lat": 23.2335, "lng": 77.4345, "demand": 130.0},
            {"name": "New Market TT Nagar", "lat": 23.2380, "lng": 77.3990, "demand": 110.0},
            {"name": "Hoshangabad Road Logistics Strip", "lat": 23.1850, "lng": 77.4650, "demand": 140.0},
            {"name": "Bairagarh Commercial Market", "lat": 23.2750, "lng": 77.3450, "demand": 120.0},
        ]
    },
    "nagpur": {
        "city_name": "Nagpur (Zero Mile Center of India)",
        "state": "Maharashtra",
        "depot": {"name": "MIHAN Multi-Modal Logistics Hub", "lat": 21.0620, "lng": 79.0520},
        "stops": [
            {"name": "Butibori Industrial Estate MIDC", "lat": 20.9250, "lng": 78.9850, "demand": 180.0},
            {"name": "Sitabuldi Central Commercial Hub", "lat": 21.1460, "lng": 79.0830, "demand": 130.0},
            {"name": "Kalamna Wholesale Grain Market", "lat": 21.1820, "lng": 79.1450, "demand": 160.0},
            {"name": "Hingna Industrial Area MIDC", "lat": 21.1050, "lng": 78.9950, "demand": 140.0},
            {"name": "Wardha Road Logistics Terminal", "lat": 21.0850, "lng": 79.0680, "demand": 120.0},
        ]
    },
    "patna": {
        "city_name": "Patna",
        "state": "Bihar",
        "depot": {"name": "Patliputra Industrial Freight Hub", "lat": 25.6320, "lng": 85.1120},
        "stops": [
            {"name": "Fatuha Industrial Logistics Area", "lat": 25.5180, "lng": 85.3120, "demand": 170.0},
            {"name": "Bailey Road Commercial Corridor", "lat": 25.6120, "lng": 85.0950, "demand": 130.0},
            {"name": "Fraser Road Central Business Zone", "lat": 25.6080, "lng": 85.1410, "demand": 120.0},
            {"name": "Didarganj Cargo Freight Terminal", "lat": 25.5650, "lng": 85.2450, "demand": 150.0},
            {"name": "Kankarbagh Commercial Strip", "lat": 25.5920, "lng": 85.1550, "demand": 110.0},
        ]
    },
    "bhubaneswar": {
        "city_name": "Bhubaneswar",
        "state": "Odisha",
        "depot": {"name": "Mancheswar Industrial Estate Hub", "lat": 20.3250, "lng": 85.8650},
        "stops": [
            {"name": "Infocity IT Corridor Chandaka", "lat": 20.3580, "lng": 85.8150, "demand": 150.0},
            {"name": "Rasulgarh Freight Square", "lat": 20.3010, "lng": 85.8720, "demand": 140.0},
            {"name": "Saheed Nagar Commercial Center", "lat": 20.2920, "lng": 85.8480, "demand": 120.0},
            {"name": "Khordha Industrial Estate", "lat": 20.1850, "lng": 85.6250, "demand": 170.0},
            {"name": "Nayapalli Tech Hub", "lat": 20.3020, "lng": 85.8180, "demand": 110.0},
        ]
    },
    "kanpur": {
        "city_name": "Kanpur",
        "state": "Uttar Pradesh",
        "depot": {"name": "Panki Industrial Logistics Hub", "lat": 26.4750, "lng": 80.2450},
        "stops": [
            {"name": "Fazalganj Industrial Estate", "lat": 26.4680, "lng": 80.3050, "demand": 160.0},
            {"name": "The Mall Central Business District", "lat": 26.4650, "lng": 80.3550, "demand": 120.0},
            {"name": "Jajmau Leather Cluster Hub", "lat": 26.4350, "lng": 80.4050, "demand": 180.0},
            {"name": "Rania Industrial Corridor", "lat": 26.4250, "lng": 80.0850, "demand": 150.0},
            {"name": "Govind Nagar Retail Hub", "lat": 26.4420, "lng": 80.3120, "demand": 110.0},
        ]
    },
    "vadodara": {
        "city_name": "Vadodara (Baroda)",
        "state": "Gujarat",
        "depot": {"name": "Makarpura GIDC Industrial Hub", "lat": 22.2520, "lng": 73.1850},
        "stops": [
            {"name": "Manjusar GIDC Chemical Corridor", "lat": 22.4550, "lng": 73.2350, "demand": 180.0},
            {"name": "Alkapuri Business District", "lat": 22.3120, "lng": 73.1750, "demand": 120.0},
            {"name": "Nandesari Industrial Area GIDC", "lat": 22.4150, "lng": 73.1150, "demand": 160.0},
            {"name": "Gorwa Industrial Estate", "lat": 22.3350, "lng": 73.1550, "demand": 130.0},
            {"name": "Waghodia Auto Components SEZ", "lat": 22.2850, "lng": 73.3850, "demand": 150.0},
        ]
    },
    "thiruvananthapuram": {
        "city_name": "Thiruvananthapuram (Trivandrum)",
        "state": "Kerala",
        "depot": {"name": "Technopark Phase 1 & 3 IT Hub", "lat": 8.5580, "lng": 76.8810},
        "stops": [
            {"name": "Vizhinjam International Seaport Hub", "lat": 8.3750, "lng": 77.0050, "demand": 190.0},
            {"name": "Kochuveli Industrial Freight Strip", "lat": 8.5080, "lng": 76.8920, "demand": 140.0},
            {"name": "East Fort Central Commercial Market", "lat": 8.4850, "lng": 76.9480, "demand": 120.0},
            {"name": "Kazhakkoottam Tech Corridor", "lat": 8.5720, "lng": 76.8680, "demand": 130.0},
            {"name": "Palayam Business District", "lat": 8.5020, "lng": 76.9520, "demand": 110.0},
        ]
    },
    "guwahati": {
        "city_name": "Guwahati (Gateway to Northeast)",
        "state": "Assam",
        "depot": {"name": "Amingaon Inland Container Depot ICD", "lat": 26.1820, "lng": 91.6750},
        "stops": [
            {"name": "GS Road Commercial High Street", "lat": 26.1550, "lng": 91.7750, "demand": 130.0},
            {"name": "Fancy Bazaar Wholesale Trade Hub", "lat": 26.1850, "lng": 91.7450, "demand": 160.0},
            {"name": "Khanapara Gateway Logistics Point", "lat": 26.1150, "lng": 91.8250, "demand": 140.0},
            {"name": "Palasbari Industrial Corridor", "lat": 26.1280, "lng": 91.5050, "demand": 150.0},
            {"name": "Dispur Capital Logistics Zone", "lat": 26.1420, "lng": 91.7920, "demand": 110.0},
        ]
    },
    "amritsar": {
        "city_name": "Amritsar",
        "state": "Punjab",
        "depot": {"name": "Attari Wagah Integrated Check Post Hub", "lat": 31.6050, "lng": 74.6050},
        "stops": [
            {"name": "Focal Point Industrial Estate", "lat": 31.6250, "lng": 74.9250, "demand": 160.0},
            {"name": "Hall Bazaar Central Trade Zone", "lat": 31.6320, "lng": 74.8750, "demand": 130.0},
            {"name": "Ranjit Avenue Commercial Plaza", "lat": 31.6580, "lng": 74.8550, "demand": 110.0},
            {"name": "Chheharta Industrial Area", "lat": 31.6380, "lng": 74.7950, "demand": 140.0},
            {"name": "Majitha Road Freight Hub", "lat": 31.6750, "lng": 74.8950, "demand": 120.0},
        ]
    },
    "dehradun": {
        "city_name": "Dehradun (Doon Valley)",
        "state": "Uttarakhand",
        "depot": {"name": "Selaqui Industrial Freight Area", "lat": 30.3650, "lng": 77.8550},
        "stops": [
            {"name": "Patel Nagar Commercial Hub", "lat": 30.3050, "lng": 78.0150, "demand": 120.0},
            {"name": "Rajpur Road Premium Business Strip", "lat": 30.3450, "lng": 78.0650, "demand": 110.0},
            {"name": "Harrawala Transport Terminal", "lat": 30.2650, "lng": 78.0950, "demand": 140.0},
            {"name": "Paltan Bazaar Central Market", "lat": 30.3220, "lng": 78.0420, "demand": 130.0},
            {"name": "Vikasnagar Agricultural Trade Zone", "lat": 30.4850, "lng": 77.7750, "demand": 150.0},
        ]
    },
    "varanasi": {
        "city_name": "Varanasi (Kashi)",
        "state": "Uttar Pradesh",
        "depot": {"name": "Ramnagar Multi-Modal Inland Port", "lat": 25.2650, "lng": 83.0350},
        "stops": [
            {"name": "Shivpur Industrial Hub", "lat": 25.3650, "lng": 82.9550, "demand": 140.0},
            {"name": "Chowk & Godowlia Central Silk Market", "lat": 25.3120, "lng": 83.0080, "demand": 130.0},
            {"name": "Lanka Commercial Strip BHU", "lat": 25.2820, "lng": 82.9980, "demand": 110.0},
            {"name": "Babatpur Airport Cargo Complex", "lat": 25.4520, "lng": 82.8580, "demand": 150.0},
            {"name": "Cantonment Commercial District", "lat": 25.3350, "lng": 82.9850, "demand": 120.0},
        ]
    },
    "raipur": {
        "city_name": "Raipur (Steel & Mining Capital)",
        "state": "Chhattisgarh",
        "depot": {"name": "Urla Industrial Growth Centre", "lat": 21.3150, "lng": 81.5950},
        "stops": [
            {"name": "Bhanpuri Logistics Freight Corridor", "lat": 21.2950, "lng": 81.6450, "demand": 170.0},
            {"name": "Naya Raipur Atal Nagar Smart Hub", "lat": 21.1650, "lng": 81.7850, "demand": 130.0},
            {"name": "Pandri Cloth Wholesale Market", "lat": 21.2580, "lng": 81.6520, "demand": 140.0},
            {"name": "Siltara Heavy Industrial Area", "lat": 21.3850, "lng": 81.6850, "demand": 180.0},
            {"name": "Jaistambh Chowk Commercial Center", "lat": 21.2420, "lng": 81.6320, "demand": 110.0},
        ]
    }
}

class IndianGeocodingService:
    _cache: Dict[str, Tuple[str, float, float, str]] = {}

    # Popular Indian logistics corridors and landmarks for instant zero-latency matching
    WELL_KNOWN_LANDMARKS = {
        "silk board": {"name": "Silk Board Junction Hub", "lat": 12.9176, "lng": 77.6238, "state": "Karnataka", "associated_hub": "bengaluru"},
        "marathahalli": {"name": "Marathahalli Bridge Logistics Hub", "lat": 12.9591, "lng": 77.6974, "state": "Karnataka", "associated_hub": "bengaluru"},
        "electronic city": {"name": "Electronic City Toll Gateway", "lat": 12.8452, "lng": 77.6602, "state": "Karnataka", "associated_hub": "bengaluru"},
        "indiranagar": {"name": "Indiranagar 100ft Road Retail", "lat": 12.9784, "lng": 77.6408, "state": "Karnataka", "associated_hub": "bengaluru"},
        "whitefield": {"name": "Whitefield ITPL Tech Corridor", "lat": 12.9698, "lng": 77.7499, "state": "Karnataka", "associated_hub": "bengaluru"},
        "koramangala": {"name": "Koramangala 4th Block Hub", "lat": 12.9352, "lng": 77.6245, "state": "Karnataka", "associated_hub": "bengaluru"},
        "peenya": {"name": "Peenya Industrial Logistics Hub", "lat": 13.0285, "lng": 77.5197, "state": "Karnataka", "associated_hub": "bengaluru"},
        "ponneri": {"name": "Ponneri Industrial Smart City", "lat": 13.3323, "lng": 80.1983, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "ambattur": {"name": "Ambattur Industrial Estate", "lat": 13.0983, "lng": 80.1623, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "sriperumbudur": {"name": "Sriperumbudur Auto Cluster Hub", "lat": 12.9675, "lng": 79.9441, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "guindy": {"name": "Guindy Industrial Estate & IT Park", "lat": 13.0067, "lng": 80.2025, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "sholinganallur": {"name": "OMR Sholinganallur Tech Corridor", "lat": 12.9010, "lng": 80.2279, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "t nagar": {"name": "T. Nagar Commercial Hub", "lat": 13.0418, "lng": 80.2341, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "adyar": {"name": "Adyar Retail Commercial Corridor", "lat": 13.0012, "lng": 80.2565, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "velachery": {"name": "Velachery Express Terminal", "lat": 12.9759, "lng": 80.2212, "state": "Tamil Nadu", "associated_hub": "chennai"},
        "bkc": {"name": "Bandra Kurla Complex (BKC)", "lat": 19.0657, "lng": 72.8687, "state": "Maharashtra", "associated_hub": "mumbai"},
        "bandra": {"name": "Bandra Kurla Complex (BKC)", "lat": 19.0657, "lng": 72.8687, "state": "Maharashtra", "associated_hub": "mumbai"},
        "andheri": {"name": "Andheri East MIDC Commercial", "lat": 19.1197, "lng": 72.8664, "state": "Maharashtra", "associated_hub": "mumbai"},
        "powai": {"name": "Powai Hiranandani Tech Hub", "lat": 19.1176, "lng": 72.9060, "state": "Maharashtra", "associated_hub": "mumbai"},
        "hinjawadi": {"name": "Hinjawadi Rajiv Gandhi Infotech Park", "lat": 18.5913, "lng": 73.7389, "state": "Maharashtra", "associated_hub": "pune"},
        "hitec city": {"name": "Hitec City Cyber Towers", "lat": 17.4504, "lng": 78.3808, "state": "Telangana", "associated_hub": "hyderabad"},
        "gachibowli": {"name": "Gachibowli Financial District", "lat": 17.4401, "lng": 78.3489, "state": "Telangana", "associated_hub": "hyderabad"},
        "gurgaon": {"name": "Gurgaon DLF Cyber City", "lat": 28.4950, "lng": 77.0895, "state": "Haryana", "associated_hub": "delhi"},
        "cyber city": {"name": "Gurgaon DLF Cyber City", "lat": 28.4950, "lng": 77.0895, "state": "Haryana", "associated_hub": "delhi"},
        "noida": {"name": "Noida Sector 62 IT Park", "lat": 28.6280, "lng": 77.3649, "state": "Uttar Pradesh", "associated_hub": "delhi"},
        "salt lake": {"name": "Salt Lake Sector V IT Hub", "lat": 22.5802, "lng": 88.4344, "state": "West Bengal", "associated_hub": "kolkata"},
        "howrah": {"name": "Howrah Freight Terminal", "lat": 22.5850, "lng": 88.3468, "state": "West Bengal", "associated_hub": "kolkata"},
    }

    @classmethod
    async def geocode_query(cls, query: str) -> Optional[Dict[str, Any]]:
        """
        Geocodes any Indian town, city, or district using curated DB + Nominatim.
        Supports natural language prompts (e.g. 'Add urgent delivery to Indiranagar 50kg').
        """
        raw_low = query.lower().strip()
        is_switch_intent = any(w in raw_low for w in ["switch", "change", "move to", "select city", "hub", "go to"])

        # 1. Check known landmark dictionary
        for landmark_key, landmark_data in cls.WELL_KNOWN_LANDMARKS.items():
            if landmark_key in raw_low:
                # If user explicitly said switch to that hub or if it's a stop
                return {
                    "name": landmark_data["name"],
                    "lat": landmark_data["lat"],
                    "lng": landmark_data["lng"],
                    "state": landmark_data["state"],
                    "is_known_hub": is_switch_intent and landmark_key in INDIAN_HUBS_DB,
                    "associated_hub": landmark_data.get("associated_hub"),
                    "hub_key": landmark_data.get("associated_hub")
                }

        # 2. Check in curated City Hubs (e.g. "chennai", "bengaluru", "mumbai")
        for key, hub in INDIAN_HUBS_DB.items():
            city_low = hub["city_name"].lower()
            if key in raw_low or city_low in raw_low or (key == "bengaluru" and "bangalore" in raw_low) or (key == "chennai" and "madras" in raw_low) or (key == "mumbai" and "bombay" in raw_low) or (key == "kolkata" and "calcutta" in raw_low):
                depot = hub["depot"]
                return {
                    "name": hub["city_name"],
                    "lat": depot["lat"],
                    "lng": depot["lng"],
                    "state": hub["state"],
                    "is_known_hub": True,
                    "hub_key": key
                }

        # 3. Check inside curated DB sub-stops
        for key, hub in INDIAN_HUBS_DB.items():
            for stop in hub["stops"]:
                stop_low = stop["name"].lower()
                # Check for significant keywords
                words = [w for w in stop_low.replace("(", " ").replace(")", " ").split() if len(w) >= 4 and w not in {"road", "tech", "park", "hub", "commercial", "industrial", "estate", "phase", "zone", "central", "retail", "express"}]
                if any(w in raw_low for w in words):
                    return {
                        "name": stop["name"],
                        "lat": stop["lat"],
                        "lng": stop["lng"],
                        "state": hub["state"],
                        "is_known_hub": False,
                        "associated_hub": key
                    }

        # 4. Clean query for live OpenStreetMap Nominatim geocoding
        # Strip common instructions & weight tokens
        import re
        clean_q = re.sub(r"(switch\s*to|switch|move\s*to|move|change\s*to|change|go\s*to|select\s*city|add\s*delivery\s*to|add\s*stop\s*at|add|urgent|delivery|deliver|to|at|in|stop|order|parcel|cargo|\d+\s*(kg|kilos|kgs)?|heavy|express|hub)", " ", raw_low)
        clean_q = re.sub(r"[^a-zA-Z\s]", " ", clean_q).strip()

        if len(clean_q) < 3:
            return None

        if clean_q in cls._cache:
            name, lat, lng, state = cls._cache[clean_q]
            return {"name": name, "lat": lat, "lng": lng, "state": state, "is_known_hub": is_switch_intent}

        try:
            url = f"https://nominatim.openstreetmap.org/search?q={clean_q}+india&format=json&limit=1&countrycodes=in"
            headers = {"User-Agent": "EcoRouteAI-India-Logistics/1.0"}
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    results = res.json()
                    if results:
                        first = results[0]
                        display_name = first.get("display_name", "")
                        lat = float(first.get("lat"))
                        lng = float(first.get("lon"))
                        
                        parts = [p.strip() for p in display_name.split(",")]
                        state = parts[-2] if len(parts) >= 2 else "India"
                        short_name = parts[0] + (f", {parts[1]}" if len(parts) > 2 else "")

                        cls._cache[clean_q] = (short_name, lat, lng, state)
                        return {
                            "name": short_name,
                            "lat": lat,
                            "lng": lng,
                            "state": state,
                            "is_known_hub": is_switch_intent
                        }
        except Exception as e:
            logger.warning(f"Nominatim geocoding failed for '{clean_q}': {e}")

        return None

