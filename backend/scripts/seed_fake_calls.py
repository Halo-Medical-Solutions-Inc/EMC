import asyncio
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models.call import Call, CallStatus, ExtractionStatus
from app.utils.encryption import encrypt_for_storage


PROVIDERS = [
    "Dr. Paul H. Janda",
    "Dr. Jay Mahajan",
    "Dr. Robert Balsiger",
    "Dr. Aroucha Vickers",
    "Dr. Steven Fan Zhang",
    "Dr. Taylor Campbell",
    "Dr. Lisa Conners",
    "Dr. Garet Zaugg",
    "Dr. Duncan Gilmour",
    "Dr. Michael Dang",
    "Dr. Azin Azma",
    "Dr. Jasmine Chopra",
    "Dr. Krupesh Bhatka",
    "Dr. Faisal Choudhury",
    "Dr. Aleksandra Ferreira",
    "Other",
    "Not Provided",
]

PRIMARY_INTENTS = [
    "Appointment (New/Reschedule/Cancel)",
    "Prescription Refill",
    "Test Results",
    "Referral Request",
    "Medical Records",
    "Billing/Insurance Question",
    "Speak to Staff",
    "Report Symptoms",
    "Prior Authorization",
    "Spam/Wrong Number",
    "Other",
    "Not Provided",
]

CALLER_AFFILIATIONS = [
    "Patient",
    "Family Member",
    "Caregiver",
    "Pharmacy",
    "Other Provider",
    "Hospital",
    "Insurance",
    "Other",
    "Not Provided",
]

PRIORITIES = ["Low", "Medium", "High", "Not Provided"]

FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
    "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
    "Kenneth", "Carol", "Kevin", "Amanda", "Brian", "Dorothy", "George", "Melissa",
    "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon",
    "Jeffrey", "Laura", "Ryan", "Cynthia", "Jacob", "Kathleen", "Gary", "Amy",
    "Nicholas", "Angela", "Eric", "Shirley", "Jonathan", "Anna", "Stephen", "Brenda",
    "Larry", "Pamela", "Justin", "Emma", "Scott", "Nicole", "Brandon", "Helen",
    "Benjamin", "Samantha", "Samuel", "Katherine", "Frank", "Christine", "Gregory", "Debra",
    "Raymond", "Rachel", "Alexander", "Carolyn", "Patrick", "Janet", "Jack", "Virginia",
    "Dennis", "Maria", "Jerry", "Heather", "Tyler", "Diane", "Aaron", "Julie",
    "Jose", "Joyce", "Henry", "Victoria", "Adam", "Kelly", "Douglas", "Christina",
    "Nathan", "Joan", "Zachary", "Evelyn", "Kyle", "Judith", "Noah", "Megan",
    "Ethan", "Cheryl", "Jeremy", "Andrea", "Walter", "Hannah", "Christian", "Jacqueline",
    "Keith", "Martha", "Roger", "Gloria", "Terry", "Teresa", "Gerald", "Sara",
    "Harold", "Janice", "Sean", "Marie", "Austin", "Julia", "Carl", "Grace",
    "Arthur", "Judy", "Lawrence", "Theresa", "Dylan", "Madison", "Jesse", "Beverly",
    "Jordan", "Denise", "Bryan", "Marilyn", "Billy", "Amber", "Joe", "Danielle",
    "Bruce", "Rose", "Gabriel", "Brittany", "Logan", "Diana", "Albert", "Abigail",
    "Alan", "Jane", "Juan", "Lori", "Wayne", "Olivia", "Roy", "Jean",
    "Ralph", "Frances", "Eugene", "Kathryn", "Louis", "Alice", "Philip", "Jasmine",
    "Johnny", "Gail", "Bobby", "Joan", "Noah", "Evelyn", "Randy", "Judith",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Sanchez",
    "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green", "Adams",
    "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
    "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards",
    "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy", "Cook", "Rogers",
    "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson", "Bailey", "Reed", "Kelly",
    "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson", "Brooks",
    "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes",
    "Price", "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross",
    "Foster", "Jimenez", "Powell", "Jenkins", "Perry", "Russell", "Sullivan", "Bell",
    "Coleman", "Butler", "Henderson", "Barnes", "Gonzales", "Fisher", "Vasquez", "Simmons",
    "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham", "Reynolds", "Griffin",
    "Wallace", "Moreno", "West", "Cole", "Hayes", "Bryant", "Herrera", "Gibson",
    "Ellis", "Tran", "Medina", "Aguilar", "Stevens", "Murray", "Ford", "Castro",
    "Marshall", "Owens", "Harrison", "Fernandez", "Mcdonald", "Woods", "Washington", "Kennedy",
    "Wells", "Vargas", "Henry", "Chen", "Freeman", "Webb", "Tucker", "Guzman",
    "Burns", "Crawford", "Olson", "Simpson", "Porter", "Hunter", "Gordon", "Mendez",
    "Silva", "Shaw", "Snyder", "Mason", "Dixon", "Munoz", "Hunt", "Hicks",
    "Holmes", "Palmer", "Wagner", "Black", "Robertson", "Boyd", "Rose", "Stone",
    "Salazar", "Fox", "Warren", "Mills", "Meyer", "Rice", "Schmidt", "Garza",
    "Daniels", "Ferguson", "Nichols", "Stephens", "Soto", "Weaver", "Ryan", "Gardner",
    "Payne", "Grant", "Dunn", "Kelley", "Spencer", "Hawkins", "Arnold", "Pierce",
    "Vazquez", "Hansen", "Peters", "Santos", "Hart", "Bradley", "Knight", "Elliott",
    "Cunningham", "Duncan", "Armstrong", "Hudson", "Carroll", "Lane", "Riley", "Andrews",
    "Alvarado", "Ray", "Delgado", "Berry", "Perkins", "Hoffman", "Johnston", "Matthews",
    "Pena", "Richards", "Contreras", "Willis", "Carpenter", "Lawrence", "Sandoval", "Guerrero",
    "George", "Chapman", "Rios", "Estrada", "Ortega", "Watkins", "Greene", "Nunez",
    "Wheeler", "Valdez", "Harper", "Lynch", "Barker", "Maldonado", "Oneal", "Summers",
    "Buchanan", "Morton", "Savage", "Dennis", "Mcgee", "Farmer", "Delacruz", "Aguirre",
    "Vega", "Glover", "Manning", "Cohen", "Harmon", "Rodgers", "Robbins", "Newton",
    "Todd", "Blair", "Higgins", "Ingram", "Reese", "Cannon", "Strickland", "Townsend",
    "Potter", "Goodwin", "Walton", "Rowe", "Hampton", "Ortega", "Patton", "Swanson",
    "Joseph", "Combs", "Petty", "Cochran", "Brewer", "Bauer", "Franklin", "Love",
    "Yates", "Beasley", "Klein", "Pratt", "Casey", "Branch", "Flowers", "Valenzuela",
    "Parks", "Mcconnell", "Watts", "Barker", "Norris", "Vaughan", "Vazquez", "Rocha",
    "Booker", "Mercado", "Cordova", "Waller", "Arellano", "Madden", "Mata", "Bonilla",
    "Stanton", "Compton", "Kaufman", "Dudley", "Mcpherson", "Beltran", "Dickson", "Mccann",
    "Villegas", "Proctor", "Hester", "Cantrell", "Daugherty", "Cherry", "Bray", "Davila",
    "Rowland", "Levine", "Madden", "Spence", "Good", "Irwin", "Werner", "Krause",
    "Petty", "Whitney", "Baird", "Hooper", "Pollard", "Zavala", "Jarvis", "Holden",
    "Haas", "Hendrix", "Mcgrath", "Bird", "Lucero", "Terrell", "Riggs", "Joyce",
    "Mercer", "Rollins", "Galloway", "Duke", "Odom", "Andersen", "Downs", "Hatfield",
    "Benitez", "Archer", "Huerta", "Travis", "Mcneil", "Hinton", "Zhang", "Hays",
    "Mayo", "Fritz", "Branch", "Mooney", "Ewing", "Ritter", "Esparza", "Frey",
    "Braun", "Gay", "Riddle", "Haney", "Kaiser", "Holder", "Chaney", "Mcknight",
    "Gamble", "Vang", "Cooley", "Carney", "Cowan", "Forbes", "Ferrell", "Davies",
    "Barajas", "Shea", "Osborn", "Bright", "Cuevas", "Bolton", "Murillo", "Lutz",
    "Duarte", "Kidd", "Key", "Cooke", "Goff", "Dejesus", "Marin", "Dotson",
    "Bonner", "Cotton", "Wise", "Gill", "Mclaughlin", "Harmon", "Hood", "Mccullough",
    "Richards", "Henson", "Cisneros", "Hale", "Hancock", "Grimes", "Glenn", "Cline",
    "Delacruz", "Camacho", "Dillon", "Parrish", "Oneill", "Melton", "Booth", "Kane",
    "Berg", "Harrell", "Pitts", "Savage", "Wiggins", "Brennan", "Salas", "Marks",
    "Russo", "Sawyer", "Baxter", "Golden", "Hutchinson", "Liu", "Walter", "Mcdowell",
    "Wiley", "Rich", "Humphrey", "Johns", "Koch", "Suarez", "Hobbs", "Beard",
    "Gilmore", "Pitts", "Mccarthy", "Durham", "Pollard", "Melendez", "Booth", "Little",
    "Fowler", "Calderon", "Santiago", "Small", "Herman", "Kramer", "Swanson", "Fuentes",
    "Bond", "Bernard", "Villarreal", "Kaufman", "Roy", "Mack", "Dickson", "Mccormick",
    "Wall", "Quinn", "Ashley", "Padilla", "Rocha", "Cabrera", "Guzman", "Warren",
    "Acevedo", "Gay", "Osborne", "Acosta", "Warner", "Pacheco", "Glass", "Abrams",
    "Odell", "Baird", "Becerra", "Saunders", "Blankenship", "Langley", "Goldstein", "Velazquez",
    "Stark", "Bowers", "Lowery", "Schmitt", "Hoover", "Perry", "Nicholson", "Underwood",
    "Tate", "Salinas", "Berg", "Shaffer", "Carroll", "Valdez", "Horn", "Sheppard",
    "Burns", "Hoover", "Gallegos", "Peterson", "Santana", "Guzman", "Morrison", "Kline",
    "Bush", "Gill", "Case", "Schroeder", "Newton", "Bartlett", "Valentine", "Mccall",
    "Tanner", "Levine", "Norris", "Mclaughlin", "Juarez", "Banks", "Orr", "Marsh",
    "Mccarty", "Cline", "Key", "Higgins", "Carrillo", "Mays", "Clay", "Daugherty",
    "Roach", "Cochran", "Pritchard", "Pate", "May", "Trevino", "Goss", "Swenson",
    "Oconnor", "Bass", "Jefferson", "Townsend", "Horton", "Pratt", "Casey", "Shepard",
    "Cardenas", "Dennis", "Sampson", "Tanner", "Atkinson", "Medina", "Lam", "Hahn",
    "Garrison", "Ewing", "Osborne", "Mercer", "Brock", "Lassiter", "Bond", "Dyer",
    "Solis", "Davies", "Solomon", "Vang", "Fontenot", "Forrest", "Frye", "Kiser",
    "Farley", "Nixon", "Mccann", "Hyde", "Pennington", "Bernstein", "Gorman", "Buck",
    "Pitts", "Crosby", "Burnett", "Lynch", "Santiago", "Carr", "Roach", "Rollins",
    "Kendrick", "Gentry", "Holloway", "Adkins", "Ortega", "Galloway", "Galvan", "Galloway",
    "Galvan", "Galloway", "Galvan", "Galloway", "Galvan", "Galloway", "Galvan", "Galloway",
]

PHONE_AREA_CODES = ["702", "725", "702", "725", "702", "725", "702", "725", "702", "725"]

TRANSCRIPT_TEMPLATES = {
    "Appointment (New/Reschedule/Cancel)": [
        "AI: Thank you for calling Memorial Cardiology. How can I help you today?\nUser: Hi, I need to schedule an appointment with {provider}.\nAI: I'd be happy to help you schedule an appointment. Can I get your name and date of birth?\nUser: My name is {caller_name} and my DOB is {patient_dob}.\nAI: Thank you. What's the reason for your visit?\nUser: I've been having headaches and my primary care doctor recommended I see a neurologist.\nAI: I understand. Let me check availability. Would you prefer morning or afternoon?\nUser: Morning would be best.\nAI: I have availability next Tuesday at 10 AM. Does that work for you?\nUser: Yes, that works perfectly.\nAI: Great, I've scheduled your appointment for {date} at 10 AM with {provider}. You'll receive a confirmation text shortly.",
        "AI: Memorial Cardiology, how can I assist you?\nUser: I need to reschedule my appointment.\nAI: I can help with that. Can I get your name?\nUser: {caller_name}.\nAI: I see your appointment is scheduled for {date}. What date would work better for you?\nUser: Can we move it to next week?\nAI: Absolutely. I have availability next Thursday at 2 PM. Would that work?\nUser: Yes, that's perfect.\nAI: Your appointment has been rescheduled to next Thursday at 2 PM. You'll receive a confirmation shortly.",
    ],
    "Prescription Refill": [
        "AI: Thank you for calling Memorial Cardiology. How can I help you?\nUser: I need a refill on my medication.\nAI: I can help with that. Can I get your name and date of birth?\nUser: {caller_name}, DOB {patient_dob}.\nAI: Thank you. Which medication do you need refilled?\nUser: I need a refill on my Topamax prescription.\nAI: I'll send a refill request to {provider}. Is this for the same pharmacy?\nUser: Yes, CVS on Main Street.\nAI: Perfect. The refill request has been sent. It should be ready in 2-3 business days.\nUser: Thank you so much.\nAI: You're welcome. Is there anything else I can help you with?\nUser: No, that's all. Thank you.",
    ],
    "Test Results": [
        "AI: Memorial Cardiology, how can I help you?\nUser: I'm calling about my test results.\nAI: I can help with that. Can I get your name and date of birth?\nUser: {caller_name}, DOB {patient_dob}.\nAI: Thank you. Which test are you calling about?\nUser: I had an MRI done last week.\nAI: I see your MRI results are in. {provider} has reviewed them and they look normal. Would you like to schedule a follow-up appointment to discuss?\nUser: Yes, please.\nAI: I have availability next week. Would Wednesday at 3 PM work?\nUser: That works for me.\nAI: Great, I've scheduled your follow-up for Wednesday at 3 PM.",
    ],
    "Report Symptoms": [
        "AI: Thank you for calling Memorial Cardiology. How can I assist you?\nUser: I'm experiencing some concerning symptoms.\nAI: I'm sorry to hear that. Can you tell me what symptoms you're experiencing?\nUser: I've been having severe headaches and some vision changes.\nAI: I understand this is concerning. Can I get your name and date of birth?\nUser: {caller_name}, DOB {patient_dob}.\nAI: Thank you. How long have you been experiencing these symptoms?\nUser: About a week now.\nAI: I'll note this for {provider}. Given the severity, I'd recommend scheduling an appointment as soon as possible. I have availability tomorrow at 2 PM.\nUser: Yes, please schedule that.\nAI: I've scheduled your appointment for tomorrow at 2 PM. If your symptoms worsen, please go to the emergency room.",
    ],
    "Billing/Insurance Question": [
        "AI: Memorial Cardiology, how can I help you?\nUser: I have a question about my bill.\nAI: I can help with billing questions. Can I get your name?\nUser: {caller_name}.\nAI: Thank you. What's your question?\nUser: I received a bill but I thought my insurance would cover it.\nAI: Let me check your account. I see you have Blue Cross Blue Shield. The claim was submitted but it looks like there's a deductible that needs to be met first.\nUser: Oh, I see. How much is the balance?\nAI: Your balance is $150. Would you like to set up a payment plan?\nUser: Yes, please.\nAI: I can set up a payment plan of $50 per month for 3 months. Does that work?\nUser: Yes, that's perfect. Thank you.",
    ],
    "Medical Records": [
        "AI: Thank you for calling Memorial Cardiology. How can I assist you?\nUser: I need to request my medical records.\nAI: I can help with that. Can I get your name and date of birth?\nUser: {caller_name}, DOB {patient_dob}.\nAI: Thank you. Where would you like the records sent?\nUser: Can you send them to my new doctor's office?\nAI: Absolutely. What's the name and address of the office?\nUser: Dr. Smith's office at 123 Main Street, Las Vegas.\nAI: I'll send a records request. It typically takes 7-10 business days. Is there a specific date you need them by?\nUser: No, that's fine. Thank you.",
    ],
    "Referral Request": [
        "AI: Memorial Cardiology, how can I help you?\nUser: I need a referral to see a specialist.\nAI: I can help with that. Can I get your name?\nUser: {caller_name}.\nAI: Thank you. What type of specialist do you need to see?\nUser: I need to see a neurosurgeon.\nAI: I'll send a referral request to {provider}. What's the reason for the referral?\nUser: My primary care doctor recommended it based on my MRI results.\nAI: I'll process the referral request. You should hear back within 3-5 business days.\nUser: Thank you so much.",
    ],
    "Prior Authorization": [
        "AI: Memorial Cardiology, how can I assist you?\nUser: I need a prior authorization for a procedure.\nAI: I can help with that. Can I get your name?\nUser: {caller_name}.\nAI: Thank you. What procedure needs authorization?\nUser: I need authorization for a Botox injection.\nAI: I'll submit a prior authorization request to your insurance. This typically takes 7-14 business days.\nUser: Okay, thank you.\nAI: You're welcome. We'll call you once we receive approval.",
    ],
    "Speak to Staff": [
        "AI: Thank you for calling Memorial Cardiology. How can I help you?\nUser: I need to speak with someone in the office.\nAI: I can help you with that. What do you need assistance with?\nUser: I have a question about my appointment.\nAI: I can help answer questions about appointments. What's your question?\nUser: I want to confirm my appointment time.\nAI: Can I get your name?\nUser: {caller_name}.\nAI: I see your appointment is scheduled for {date} at 10 AM with {provider}.\nUser: Perfect, thank you.\nAI: You're welcome. Is there anything else?\nUser: No, that's all.",
    ],
    "Spam/Wrong Number": [
        "AI: Thank you for calling Memorial Cardiology. How can I help you?\nUser: Is this Pizza Hut?\nAI: No, this is Memorial Cardiology. I think you may have dialed the wrong number.\nUser: Oh, sorry about that.\nAI: No problem. Have a good day.",
    ],
    "Other": [
        "AI: Memorial Cardiology, how can I assist you?\nUser: I have a general question.\nAI: I'm happy to help. What's your question?\nUser: What are your office hours?\nAI: Our office hours are Monday through Friday, 8 AM to 5 PM.\nUser: Thank you.\nAI: You're welcome. Is there anything else?\nUser: No, that's all.",
    ],
}

SUMMARY_TEMPLATES = {
    "Appointment (New/Reschedule/Cancel)": [
        "Pt {caller_name} scheduled appt with {provider} for {date}",
        "Pt {caller_name} rescheduled appt to {date}",
        "Pt {caller_name} cancelled appt",
    ],
    "Prescription Refill": [
        "Pt {caller_name} requested refill for Topamax",
        "Pt {caller_name} needs refill for Keppra",
        "Pt {caller_name} requested refill for Gabapentin",
    ],
    "Test Results": [
        "Pt {caller_name} calling about MRI results - normal",
        "Pt {caller_name} asking about EEG results",
        "Pt {caller_name} requesting test results",
    ],
    "Report Symptoms": [
        "Pt {caller_name} reporting headaches and vision changes - urgent appt scheduled",
        "Pt {caller_name} reporting new symptoms",
        "Pt {caller_name} calling about concerning symptoms",
    ],
    "Billing/Insurance Question": [
        "Pt {caller_name} has billing question - $150 balance, payment plan set up",
        "Pt {caller_name} insurance question",
        "Pt {caller_name} calling about bill",
    ],
    "Medical Records": [
        "Pt {caller_name} requesting medical records to be sent",
        "Pt {caller_name} needs records sent to new provider",
        "Pt {caller_name} requesting records",
    ],
    "Referral Request": [
        "Pt {caller_name} needs referral to neurosurgeon",
        "Pt {caller_name} requesting referral",
        "Pt {caller_name} needs specialist referral",
    ],
    "Prior Authorization": [
        "Pt {caller_name} needs prior auth for Botox injection",
        "Pt {caller_name} requesting prior authorization",
        "Pt {caller_name} needs auth for procedure",
    ],
    "Speak to Staff": [
        "Pt {caller_name} wants to confirm appt time",
        "Pt {caller_name} calling with general question",
        "Pt {caller_name} needs to speak with staff",
    ],
    "Spam/Wrong Number": [
        "Wrong number - caller looking for Pizza Hut",
        "Spam call",
        "Wrong number",
    ],
    "Other": [
        "Pt {caller_name} asking about office hours",
        "Pt {caller_name} general question",
        "Pt {caller_name} calling with question",
    ],
}


def generate_phone_number() -> str:
    area_code = random.choice(PHONE_AREA_CODES)
    exchange = random.randint(200, 999)
    number = random.randint(1000, 9999)
    return f"+1{area_code}{exchange}{number}"


def generate_dob() -> str:
    year = random.randint(1940, 2005)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    return f"{month:02d}/{day:02d}/{year}"


def generate_name() -> tuple[str, str]:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return first, last


def generate_transcript(intent: str, caller_name: str, patient_dob: str, provider: str) -> str:
    templates = TRANSCRIPT_TEMPLATES.get(intent, TRANSCRIPT_TEMPLATES["Other"])
    template = random.choice(templates)
    date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%B %d")
    return template.format(
        caller_name=caller_name,
        patient_dob=patient_dob,
        provider=provider,
        date=date,
    )


def generate_summary(intent: str, caller_name: str, provider: str) -> str:
    templates = SUMMARY_TEMPLATES.get(intent, SUMMARY_TEMPLATES["Other"])
    template = random.choice(templates)
    date = (datetime.now() - timedelta(days=random.randint(1, 30))).strftime("%m/%d")
    return template.format(caller_name=caller_name, provider=provider, date=date)


async def seed_fake_calls(db, num_calls: int = 100) -> None:
    print(f"Generating {num_calls} fake calls...")

    for i in range(num_calls):
        first_name, last_name = generate_name()
        caller_name = f"{first_name} {last_name}"
        patient_name = caller_name if random.random() > 0.3 else f"{random.choice(FIRST_NAMES)} {last_name}"
        patient_dob = generate_dob()
        phone_number = generate_phone_number()
        provider = random.choice(PROVIDERS)
        intent = random.choice(PRIMARY_INTENTS)
        affiliation = random.choice(CALLER_AFFILIATIONS)
        priority = random.choice(PRIORITIES)
        is_reviewed = random.random() > 0.6
        status = CallStatus.COMPLETED

        created_at = datetime.now(timezone.utc) - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        duration_seconds = random.randint(30, 600)

        transcript = generate_transcript(intent, caller_name, patient_dob, provider)
        summary = generate_summary(intent, caller_name, provider)

        vapi_data = {
            "type": "end-of-call-report",
            "call": {
                "id": f"vapi_call_{i}_{random.randint(1000, 9999)}",
                "customer": {
                    "number": phone_number,
                },
                "durationSeconds": duration_seconds,
            },
            "analysis": {
                "structuredData": {
                    "caller_name": caller_name,
                    "caller_affiliation": affiliation,
                    "patient_name": patient_name,
                    "patient_dob": patient_dob,
                    "provider_name": provider,
                    "primary_intent": intent,
                    "priority": priority,
                },
            },
            "artifact": {
                "transcript": transcript,
                "recordingUrl": f"https://example.com/recordings/call_{i}.mp3",
            },
            "durationSeconds": duration_seconds,
        }

        extraction_data = {
            "caller_name": caller_name,
            "caller_affiliation": affiliation,
            "patient_name": patient_name,
            "patient_dob": patient_dob,
            "provider_name": provider,
            "primary_intent": intent,
            "priority": priority,
            "summary": summary,
        }

        encrypted_vapi_data, vapi_kid = encrypt_for_storage(json.dumps(vapi_data))
        encrypted_extraction_data, extraction_kid = encrypt_for_storage(json.dumps(extraction_data))

        call = Call(
            twilio_call_sid=f"CA{random.randint(1000000000000000000, 9999999999999999999)}",
            vapi_call_id=vapi_data["call"]["id"],
            vapi_data_encrypted=encrypted_vapi_data,
            vapi_data_kid=vapi_kid,
            extraction_data_encrypted=encrypted_extraction_data,
            extraction_data_kid=extraction_kid,
            extraction_status=ExtractionStatus.COMPLETED,
            status=status,
            is_reviewed=is_reviewed,
            created_at=created_at,
            updated_at=created_at + timedelta(seconds=duration_seconds),
        )

        db.add(call)

        if (i + 1) % 10 == 0:
            await db.commit()
            print(f"Created {i + 1} calls...")

    await db.commit()
    print(f"Successfully created {num_calls} fake calls!")


async def main() -> None:
    print("Seeding fake call data...")
    print("-" * 40)

    async with AsyncSessionLocal() as db:
        await seed_fake_calls(db, num_calls=100)

    print("-" * 40)
    print("Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
