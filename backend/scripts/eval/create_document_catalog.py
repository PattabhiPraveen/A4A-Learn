import csv
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "metadata"
    / "evaluation"
    / "document_catalog.csv"
)


documents = [
    # ---------------------------------------------------------
    # Accessibility & Indian Sign Language - 15
    # ---------------------------------------------------------
    ("DOC001", "Introduction to Indian Sign Language", "Accessibility & ISL", "ISL", "Introduction"),
    ("DOC002", "ISL Alphabet Basics", "Accessibility & ISL", "ISL", "Alphabet"),
    ("DOC003", "Hand Shapes in ISL", "Accessibility & ISL", "ISL", "Hand Shapes"),
    ("DOC004", "Hand Orientation in Sign Language", "Accessibility & ISL", "ISL", "Orientation"),
    ("DOC005", "Hand Movement and Meaning", "Accessibility & ISL", "ISL", "Movement"),
    ("DOC006", "Facial Expressions in Sign Language", "Accessibility & ISL", "ISL", "Non-manual Markers"),
    ("DOC007", "Visual Communication for Deaf Learners", "Accessibility & ISL", "Accessibility", "Visual Communication"),
    ("DOC008", "Learning Sign Language Effectively", "Accessibility & ISL", "ISL Learning", "Practice Methods"),
    ("DOC009", "Alphabet to Word Progression", "Accessibility & ISL", "ISL Learning", "Learning Progression"),
    ("DOC010", "Sign Recognition and Feedback", "Accessibility & ISL", "ISL Learning", "Feedback"),
    ("DOC011", "Captions and Accessible Learning", "Accessibility & ISL", "Accessibility", "Captions"),
    ("DOC012", "Inclusive Digital Learning", "Accessibility & ISL", "Accessibility", "Inclusive Education"),
    ("DOC013", "Communication Needs of Deaf Learners", "Accessibility & ISL", "Accessibility", "Learner Needs"),
    ("DOC014", "Visual Learning Strategies", "Accessibility & ISL", "Accessibility", "Learning Strategies"),
    ("DOC015", "Responsible AI for Accessible Education", "Accessibility & ISL", "Responsible AI", "Accessibility"),

    # ---------------------------------------------------------
    # Python Programming - 20
    # ---------------------------------------------------------
    ("DOC016", "Introduction to Python", "Python Programming", "Python", "Basics"),
    ("DOC017", "Python Variables and Data Types", "Python Programming", "Python", "Variables"),
    ("DOC018", "Python Operators", "Python Programming", "Python", "Operators"),
    ("DOC019", "Python Conditional Statements", "Python Programming", "Control Flow", "Conditions"),
    ("DOC020", "Python For Loops", "Python Programming", "Control Flow", "For Loop"),
    ("DOC021", "Python While Loops", "Python Programming", "Control Flow", "While Loop"),
    ("DOC022", "Loop Control Statements", "Python Programming", "Control Flow", "Break and Continue"),
    ("DOC023", "Python Functions", "Python Programming", "Python", "Functions"),
    ("DOC024", "Function Parameters and Return Values", "Python Programming", "Functions", "Parameters"),
    ("DOC025", "Python Lists", "Python Programming", "Collections", "Lists"),
    ("DOC026", "Python Tuples", "Python Programming", "Collections", "Tuples"),
    ("DOC027", "Python Dictionaries", "Python Programming", "Collections", "Dictionaries"),
    ("DOC028", "Python Sets", "Python Programming", "Collections", "Sets"),
    ("DOC029", "List Comprehensions", "Python Programming", "Python", "Comprehensions"),
    ("DOC030", "Python String Processing", "Python Programming", "Python", "Strings"),
    ("DOC031", "File Handling in Python", "Python Programming", "Python", "Files"),
    ("DOC032", "Exception Handling", "Python Programming", "Python", "Exceptions"),
    ("DOC033", "Python Modules and Packages", "Python Programming", "Python", "Modules"),
    ("DOC034", "Object-Oriented Programming in Python", "Python Programming", "Python", "OOP"),
    ("DOC035", "Python Classes and Objects", "Python Programming", "OOP", "Classes"),

    # ---------------------------------------------------------
    # Data Science - 15
    # ---------------------------------------------------------
    ("DOC036", "Introduction to Data Science", "Data Science", "Data Science", "Overview"),
    ("DOC037", "Data Collection", "Data Science", "Data Science", "Acquisition"),
    ("DOC038", "Data Cleaning", "Data Science", "Data Preparation", "Cleaning"),
    ("DOC039", "Missing Value Handling", "Data Science", "Data Preparation", "Missing Data"),
    ("DOC040", "Data Transformation", "Data Science", "Data Preparation", "Transformation"),
    ("DOC041", "Exploratory Data Analysis", "Data Science", "Data Analysis", "EDA"),
    ("DOC042", "Descriptive Statistics", "Data Science", "Statistics", "Descriptive"),
    ("DOC043", "Data Visualization Fundamentals", "Data Science", "Visualization", "Basics"),
    ("DOC044", "Feature Engineering", "Data Science", "Data Science", "Features"),
    ("DOC045", "Categorical Data Encoding", "Data Science", "Preprocessing", "Encoding"),
    ("DOC046", "Data Normalization and Scaling", "Data Science", "Preprocessing", "Scaling"),
    ("DOC047", "Training and Test Data", "Data Science", "Data Science", "Data Splitting"),
    ("DOC048", "Data Leakage", "Data Science", "Data Science", "Leakage"),
    ("DOC049", "Data Quality", "Data Science", "Data Governance", "Quality"),
    ("DOC050", "Reproducible Data Science", "Data Science", "Data Science", "Reproducibility"),

    # ---------------------------------------------------------
    # Machine Learning - 15
    # ---------------------------------------------------------
    ("DOC051", "Introduction to Machine Learning", "Machine Learning", "ML", "Overview"),
    ("DOC052", "Supervised Learning", "Machine Learning", "ML", "Supervised"),
    ("DOC053", "Unsupervised Learning", "Machine Learning", "ML", "Unsupervised"),
    ("DOC054", "Classification Problems", "Machine Learning", "ML", "Classification"),
    ("DOC055", "Regression Problems", "Machine Learning", "ML", "Regression"),
    ("DOC056", "Decision Trees", "Machine Learning", "ML Algorithms", "Trees"),
    ("DOC057", "Random Forest", "Machine Learning", "ML Algorithms", "Ensemble"),
    ("DOC058", "Logistic Regression", "Machine Learning", "ML Algorithms", "Classification"),
    ("DOC059", "Support Vector Machines", "Machine Learning", "ML Algorithms", "SVM"),
    ("DOC060", "K-Nearest Neighbors", "Machine Learning", "ML Algorithms", "KNN"),
    ("DOC061", "Model Training", "Machine Learning", "ML", "Training"),
    ("DOC062", "Model Validation", "Machine Learning", "ML", "Validation"),
    ("DOC063", "Accuracy Precision and Recall", "Machine Learning", "ML Evaluation", "Metrics"),
    ("DOC064", "F1 Score and Class Imbalance", "Machine Learning", "ML Evaluation", "F1"),
    ("DOC065", "Overfitting and Underfitting", "Machine Learning", "ML", "Generalization"),

    # ---------------------------------------------------------
    # AI & Generative AI - 10
    # ---------------------------------------------------------
    ("DOC066", "Introduction to Artificial Intelligence", "AI & Generative AI", "AI", "Overview"),
    ("DOC067", "Generative AI Fundamentals", "AI & Generative AI", "Generative AI", "Fundamentals"),
    ("DOC068", "Large Language Models", "AI & Generative AI", "Generative AI", "LLM"),
    ("DOC069", "Embeddings", "AI & Generative AI", "Generative AI", "Embeddings"),
    ("DOC070", "Vector Databases", "AI & Generative AI", "RAG", "Vector Store"),
    ("DOC071", "Retrieval-Augmented Generation", "AI & Generative AI", "RAG", "Architecture"),
    ("DOC072", "Chunking for RAG", "AI & Generative AI", "RAG", "Chunking"),
    ("DOC073", "Semantic Search", "AI & Generative AI", "RAG", "Retrieval"),
    ("DOC074", "AI Hallucinations", "AI & Generative AI", "Responsible AI", "Hallucination"),
    ("DOC075", "Responsible AI Principles", "AI & Generative AI", "Responsible AI", "Principles"),

    # ---------------------------------------------------------
    # Computer Fundamentals - 10
    # ---------------------------------------------------------
    ("DOC076", "Introduction to Computer Systems", "Computer Fundamentals", "Computers", "Basics"),
    ("DOC077", "CPU and Processing", "Computer Fundamentals", "Hardware", "CPU"),
    ("DOC078", "Computer Memory", "Computer Fundamentals", "Hardware", "Memory"),
    ("DOC079", "Storage Devices", "Computer Fundamentals", "Hardware", "Storage"),
    ("DOC080", "Operating Systems", "Computer Fundamentals", "Systems", "OS"),
    ("DOC081", "Computer Networks", "Computer Fundamentals", "Networking", "Basics"),
    ("DOC082", "IP Addressing", "Computer Fundamentals", "Networking", "IP"),
    ("DOC083", "Internet Fundamentals", "Computer Fundamentals", "Networking", "Internet"),
    ("DOC084", "Cybersecurity Basics", "Computer Fundamentals", "Security", "Fundamentals"),
    ("DOC085", "Authentication and Authorization", "Computer Fundamentals", "Security", "Identity"),

    # ---------------------------------------------------------
    # Mathematics & Statistics - 10
    # ---------------------------------------------------------
    ("DOC086", "Mean Median and Mode", "Mathematics & Statistics", "Statistics", "Central Tendency"),
    ("DOC087", "Variance and Standard Deviation", "Mathematics & Statistics", "Statistics", "Dispersion"),
    ("DOC088", "Probability Basics", "Mathematics & Statistics", "Probability", "Fundamentals"),
    ("DOC089", "Conditional Probability", "Mathematics & Statistics", "Probability", "Conditional"),
    ("DOC090", "Correlation", "Mathematics & Statistics", "Statistics", "Correlation"),
    ("DOC091", "Linear Algebra Basics", "Mathematics & Statistics", "Mathematics", "Linear Algebra"),
    ("DOC092", "Vectors", "Mathematics & Statistics", "Mathematics", "Vectors"),
    ("DOC093", "Matrices", "Mathematics & Statistics", "Mathematics", "Matrices"),
    ("DOC094", "Functions in Mathematics", "Mathematics & Statistics", "Mathematics", "Functions"),
    ("DOC095", "Optimization Fundamentals", "Mathematics & Statistics", "Mathematics", "Optimization"),

    # ---------------------------------------------------------
    # Digital Learning - 5
    # ---------------------------------------------------------
    ("DOC096", "Digital Learning Fundamentals", "Digital Learning", "Education", "Digital Learning"),
    ("DOC097", "Personalized Learning", "Digital Learning", "Education", "Personalization"),
    ("DOC098", "Learning Analytics", "Digital Learning", "Education", "Analytics"),
    ("DOC099", "Accessible User Interfaces", "Digital Learning", "Accessibility", "UI"),
    ("DOC100", "AI Tutors in Education", "Digital Learning", "AI Education", "AI Tutor"),
]


FIELDNAMES = [
    "document_id",
    "title",
    "domain",
    "topic",
    "subtopic",
    "difficulty",
    "source_type",
    "source_reference",
    "license",
    "word_target",
    "expected_questions",
    "validation_status",
    "notes",
]


def main():

    rows = []

    for (
        document_id,
        title,
        domain,
        topic,
        subtopic,
    ) in documents:

        rows.append(
            {
                "document_id": document_id,
                "title": title,
                "domain": domain,
                "topic": topic,
                "subtopic": subtopic,
                "difficulty": "Beginner",
                "source_type": "benchmark",
                "source_reference": "",
                "license": "internal-benchmark",
                "word_target": 800,
                "expected_questions": 10,
                "validation_status": "pending",
                "notes": "",
            }
        )

    # ---------------------------------------------------------
    # Safety checks before writing catalog
    # ---------------------------------------------------------

    if len(rows) != 100:
        raise ValueError(
            f"Expected 100 documents, found {len(rows)}."
        )

    ids = [
        row["document_id"]
        for row in rows
    ]

    if len(ids) != len(set(ids)):
        raise ValueError(
            "Duplicate document IDs detected."
        )

    titles = [
        row["title"].lower().strip()
        for row in rows
    ]

    if len(titles) != len(set(titles)):
        raise ValueError(
            "Duplicate document titles detected."
        )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
        )

        writer.writeheader()
        writer.writerows(rows)

    print("=" * 70)
    print("A4A Learn - Document Catalog")
    print("=" * 70)
    print(f"Documents created : {len(rows)}")
    print(f"Output            : {OUTPUT_FILE}")
    print("Status            : PASS")
    print("=" * 70)


if __name__ == "__main__":
    main()