from datetime import datetime, timezone, timedelta

def _days_from_now(n: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=n)).strftime("%b %d, %Y")

# Static catalog of sample UW Bothell campus events.
# Keyed by event_id so the recommender can reference them by ID.
EVENTS: list[dict] = [
    # Technology
    {"id": "evt-001", "title": "CS Club: Intro to Machine Learning", "category": "technology", "building": "UW1", "date": _days_from_now(3), "description": "Hands-on workshop covering supervised learning basics with scikit-learn."},
    {"id": "evt-002", "title": "Hackathon Kickoff — Build for Good", "category": "technology", "building": "Discovery Hall", "date": _days_from_now(5), "description": "48-hour hackathon focused on civic tech projects. All skill levels welcome."},
    {"id": "evt-003", "title": "Cybersecurity Panel: Career Paths in InfoSec", "category": "technology", "building": "UW2", "date": _days_from_now(7), "description": "Alumni panel covering red team, blue team, and GRC career tracks."},
    {"id": "evt-004", "title": "Web Dev Workshop: React & Next.js", "category": "technology", "building": "DISC", "date": _days_from_now(10), "description": "Build a full-stack app from scratch in 2 hours."},
    # Science
    {"id": "evt-005", "title": "Biology Research Symposium", "category": "science", "building": "Science Building", "date": _days_from_now(4), "description": "Undergraduate research presentations covering ecology, cell biology, and genetics."},
    {"id": "evt-006", "title": "Astronomy Night: Spring Sky Tour", "category": "science", "building": "Quad", "date": _days_from_now(6), "description": "Telescope viewing session with the Physics club. Free hot chocolate."},
    {"id": "evt-007", "title": "Environmental Science Field Day", "category": "science", "building": "North Creek Wetlands", "date": _days_from_now(9), "description": "Water quality sampling and wetland ecology walk led by faculty."},
    # Business
    {"id": "evt-008", "title": "Entrepreneurship Speaker Series", "category": "business", "building": "UW1", "date": _days_from_now(2), "description": "Founder of a Seattle-based startup shares lessons from their first year."},
    {"id": "evt-009", "title": "Resume & LinkedIn Workshop", "category": "business", "building": "Career Services", "date": _days_from_now(4), "description": "Career center staff review resumes and LinkedIn profiles live."},
    {"id": "evt-010", "title": "Finance Club: Stock Pitch Competition", "category": "business", "building": "UW2", "date": _days_from_now(8), "description": "Teams pitch stocks to a panel of judges. Cash prizes for top 3."},
    # Arts & Culture
    {"id": "evt-011", "title": "Spring Art Show — Student Gallery", "category": "arts", "building": "CC1", "date": _days_from_now(1), "description": "Year-end showcase of student visual art, photography, and digital media."},
    {"id": "evt-012", "title": "Film Screening: Pacific Rim Documentaries", "category": "arts", "building": "Discovery Hall", "date": _days_from_now(5), "description": "Two short documentaries followed by a Q&A with the filmmakers."},
    {"id": "evt-013", "title": "Open Mic Night", "category": "arts", "building": "Husky Hall", "date": _days_from_now(11), "description": "Music, spoken word, and comedy. Sign up at the door."},
    # Health & Wellness
    {"id": "evt-014", "title": "Mental Health Awareness Fair", "category": "health", "building": "Student Union", "date": _days_from_now(3), "description": "Resources, activities, and conversations around student mental wellness."},
    {"id": "evt-015", "title": "Mindfulness & Meditation Drop-In", "category": "health", "building": "Recreation Center", "date": _days_from_now(2), "description": "20-minute guided meditation session. No experience needed."},
    {"id": "evt-016", "title": "Nutrition 101: Eating Well on a Budget", "category": "health", "building": "CC2", "date": _days_from_now(6), "description": "Dietitian-led workshop on affordable healthy eating for students."},
    # Social & Community
    {"id": "evt-017", "title": "International Food Festival", "category": "social", "building": "Quad", "date": _days_from_now(7), "description": "Student cultural clubs share food and traditions from around the world."},
    {"id": "evt-018", "title": "Game Night — Board Games & More", "category": "social", "building": "Husky Hall", "date": _days_from_now(4), "description": "Casual evening with board games, card games, and snacks."},
    {"id": "evt-019", "title": "Transfer Student Meetup", "category": "social", "building": "Student Union", "date": _days_from_now(3), "description": "Connect with other transfer students and get tips for navigating UWB."},
    # Sports & Outdoors
    {"id": "evt-020", "title": "Intramural Soccer Sign-Ups", "category": "sports", "building": "Recreation Center", "date": _days_from_now(1), "description": "Sign up your team for the spring intramural soccer league."},
]

EVENTS_BY_ID: dict[str, dict] = {e["id"]: e for e in EVENTS}

# Maps declared UW major keywords to event categories for cold-start seeding.
MAJOR_TO_CATEGORIES: dict[str, list[str]] = {
    "css": ["technology", "business"],
    "csse": ["technology"],
    "computer": ["technology"],
    "business": ["business", "social"],
    "accounting": ["business"],
    "biology": ["science", "health"],
    "chemistry": ["science"],
    "physics": ["science", "technology"],
    "psychology": ["health", "social"],
    "nursing": ["health", "science"],
    "education": ["social", "arts"],
    "english": ["arts", "social"],
    "math": ["science", "technology"],
    "environmental": ["science"],
    "art": ["arts"],
    "film": ["arts"],
    "sociology": ["social"],
    "economics": ["business"],
}


def get_events_by_categories(categories: list[str], limit: int = 10) -> list[dict]:
    matched = [e for e in EVENTS if e["category"] in categories]
    return matched[:limit]


def infer_categories_from_major(major: str) -> list[str]:
    major_lower = major.lower()
    for keyword, cats in MAJOR_TO_CATEGORIES.items():
        if keyword in major_lower:
            return cats
    return []
