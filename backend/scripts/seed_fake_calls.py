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
    "Dr. Bertolucci",
    "Dr. Prescott",
    "Dr. Thinda",
    "Dr. Teasley",
    "Dr. Mehta",
    "Dr. Ghajar",
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

PHONE_AREA_CODES = ["559", "559", "559", "559", "559", "559", "559", "559", "559", "559"]

TRANSCRIPT_TEMPLATES = {
    "Appointment (New/Reschedule/Cancel)": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: Hi, I need to schedule an appointment with {provider}.\nAI: Of course — let me get some details so the team can get that set up for you. Can I get your name?\nUser: {caller_name}.\nAI: Got it. And what's your date of birth?\nUser: {patient_dob}.\nAI: Okay. Do you have a date that was offered to you for your appointment?\nUser: They mentioned {date}.\nAI: Alright, I've got everything noted. Someone from the team will reach out to confirm your appointment. Is the number you're calling from the best one to reach you at?\nUser: Yes, that's fine.\nAI: Sounds good. We'll be in touch. Thank you, {caller_name}.",
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I need to reschedule my appointment with {provider}.\nAI: Of course. Can I get your name?\nUser: {caller_name}.\nAI: And your date of birth?\nUser: {patient_dob}.\nAI: Got it. I'll note that you need to reschedule. Someone from the team will reach out to get that set up for you. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Alright, we'll be in touch. Thank you, {caller_name}.",
    ],
    "Prescription Refill": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I need a refill on my eye drops.\nAI: Of course — which medication do you need refilled?\nUser: My prednisolone drops.\nAI: Got it. Which pharmacy do you use?\nUser: CVS on Herndon.\nAI: And which doctor is the prescription through?\nUser: {provider}.\nAI: Okay. Can I get your name?\nUser: {caller_name}.\nAI: And your date of birth?\nUser: {patient_dob}.\nAI: Alright, I've got everything noted. Someone from the team will take care of this and get back to you. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Sounds good. We'll be in touch. Thank you, {caller_name}.",
    ],
    "Test Results": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I'm calling about my OCT results.\nAI: Of course. Can I get your name?\nUser: {caller_name}.\nAI: And your date of birth?\nUser: {patient_dob}.\nAI: Which provider do you see here?\nUser: {provider}.\nAI: Got it. I'll note that you're asking about your OCT results. Someone from the team will reach out with an update. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Alright, we'll be in touch. Thank you, {caller_name}.",
    ],
    "Report Symptoms": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I'm having some discomfort in my eye after my injection.\nAI: Oh, I'm sorry to hear that. Can I get your name?\nUser: {caller_name}.\nAI: What's your date of birth?\nUser: {patient_dob}.\nAI: Which provider do you see here?\nUser: {provider}.\nAI: Were you recently injected, or have you had surgery?\nUser: I had an injection a couple days ago.\nAI: How long have you been having the discomfort?\nUser: Since yesterday.\nAI: Which eye is affected?\nUser: My right eye.\nAI: Okay. Have you tried anything for it, like artificial tears?\nUser: No, not yet.\nAI: Okay, I've got all of that noted. Someone from the team will reach out to you as soon as possible. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Sounds good. We'll be in touch. Thank you, {caller_name}.",
    ],
    "Billing/Insurance Question": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I have a question about my bill.\nAI: Sure — let me get you over to our billing department right now. One moment.\nUser: Thank you.",
    ],
    "Medical Records": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I need to request my medical records.\nAI: Of course. Can I get your name and date of birth?\nUser: {caller_name}, DOB {patient_dob}.\nAI: And where would you like the records sent?\nUser: To my new doctor's office on Shaw Avenue in Fresno.\nAI: Got it. I'll note that for the team. Someone will reach out to follow up. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Alright, we'll be in touch. Thank you, {caller_name}.",
    ],
    "Referral Request": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I'm calling about a referral.\nAI: Of course — is this about a referral coming into Eye Medical Center from another practice, or about a referral that was sent out from our office?\nUser: It was sent out from your office.\nAI: Got it. Can I get your name?\nUser: {caller_name}.\nAI: And your date of birth?\nUser: {patient_dob}.\nAI: Which provider do you see here?\nUser: {provider}.\nAI: Do you know where the referral was sent?\nUser: I think it was to a glaucoma specialist.\nAI: Alright, I've got everything noted. Someone from the team will reach out with an update. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Sounds good. We'll be in touch. Thank you, {caller_name}.",
    ],
    "Prior Authorization": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I need a prior authorization for my injection.\nAI: Of course. Can I get your name?\nUser: {caller_name}.\nAI: And your date of birth?\nUser: {patient_dob}.\nAI: Which provider do you see here?\nUser: {provider}.\nAI: Got it. I'll note that you need a prior auth for your injection. Someone from the team will follow up. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Alright, we'll be in touch. Thank you, {caller_name}.",
    ],
    "Speak to Staff": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I need to speak with someone about my appointment.\nAI: I can take down your info and make sure someone from the team reaches out. Can I get your name?\nUser: {caller_name}.\nAI: And which provider do you see here?\nUser: {provider}.\nAI: Got it. What's the question about your appointment?\nUser: I just want to confirm the time.\nAI: I'll note that. Someone will call you back to confirm. Is the number you're calling from the best one to reach you?\nUser: Yes.\nAI: Sounds good. We'll be in touch. Thank you, {caller_name}.",
    ],
    "Spam/Wrong Number": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: Oh, sorry, I think I have the wrong number.\nAI: No problem at all. Have a good day!",
    ],
    "Other": [
        "AI: Hello, you've reached Eye Medical Center of Fresno. This is Kaitlin. How can I help you?\nUser: I have a quick question — what are your office hours?\nAI: We're open Monday through Friday, 8 AM to 5 PM.\nUser: Thank you.\nAI: You're welcome. Is there anything else I can help with?\nUser: No, that's all. Thanks!",
    ],
}

SUMMARY_TEMPLATES = {
    "Appointment (New/Reschedule/Cancel)": [
        "{caller_name} called to schedule a retina appointment with {provider} for {date}. Team will follow up to confirm.",
        "{caller_name} called to reschedule appointment with {provider}. Team will follow up with new date.",
        "{caller_name} called to cancel appointment with {provider}.",
    ],
    "Prescription Refill": [
        "{caller_name} called to request a refill of prednisolone drops through {provider}. Sent to CVS on Herndon.",
        "{caller_name} called to request a refill of artificial tears through {provider}.",
        "{caller_name} called to request a refill of eye drops through {provider}. Team will follow up.",
    ],
    "Test Results": [
        "{caller_name} called asking about OCT results from {provider}. Team will follow up.",
        "{caller_name} called asking about visual field test results from {provider}.",
        "{caller_name} called requesting test results from {provider}.",
    ],
    "Report Symptoms": [
        "{caller_name} called reporting right eye discomfort after injection with {provider}. Mild, one day. Team will follow up.",
        "{caller_name} called reporting post-injection soreness with {provider}. Team will follow up.",
        "{caller_name} called reporting eye irritation. Sees {provider}. Team will follow up.",
    ],
    "Billing/Insurance Question": [
        "{caller_name} called with a billing question. Transferred to billing department.",
        "{caller_name} called about insurance coverage. Transferred to billing.",
        "{caller_name} called about a statement. Transferred to billing.",
    ],
    "Medical Records": [
        "{caller_name} called requesting medical records be sent to another provider in Fresno.",
        "{caller_name} called requesting records from {provider}.",
        "{caller_name} called requesting medical records.",
    ],
    "Referral Request": [
        "{caller_name} called checking on outgoing referral status from {provider} to a glaucoma specialist.",
        "{caller_name} called about a referral from {provider}. Team will follow up.",
        "{caller_name} called about referral status. Sees {provider}.",
    ],
    "Prior Authorization": [
        "{caller_name} called needing prior auth for injection with {provider}. Team will follow up.",
        "{caller_name} called requesting prior authorization for procedure with {provider}.",
        "{caller_name} called about prior auth status with {provider}.",
    ],
    "Speak to Staff": [
        "{caller_name} called wanting to confirm appointment time with {provider}. Team will call back.",
        "{caller_name} called with a question for {provider}'s team.",
        "{caller_name} called needing to speak with staff about {provider}.",
    ],
    "Spam/Wrong Number": [
        "Wrong number — caller dialed incorrectly.",
        "Spam call — no patient interaction.",
        "Wrong number.",
    ],
    "Other": [
        "{caller_name} called asking about office hours. Answered directly.",
        "{caller_name} called with a general question about the practice.",
        "{caller_name} called asking for the address.",
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
                "recordingUrl": f"https://storage.vapi.ai/recordings/fake_call_{i}.mp3",
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
