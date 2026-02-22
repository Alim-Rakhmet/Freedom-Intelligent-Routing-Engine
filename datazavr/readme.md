## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Framework:** Django 5.x / Django REST Framework
* **Database:**  PostgreSQL (Production)

---

## 🏗 Getting Started

Follow these steps to set up the project locally.

### 1. Environment Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/Alim-Rakhmet/Freedom-Intelligent-Routing-Engine/tree/main
cd datazavr
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```

### 2. Database Initialization

Run the following commands to prepare the database schema and load initial data:

1. **Generate migrations:** Scan models for changes.
```bash
python3 manage.py makemigrations api

```


2. **Apply migrations:** Create tables in the database.
```bash
python3 manage.py migrate

```


3. **Seed data:** Populate the database with initial/test records.
```bash
python3 manage.py load_base_data

```



### 3. Running the Server

Start the development server:

```bash
python3 manage.py runserver

```

The API will be available at: `http://127.0.0.1:8000/`

---

## 📂 Project Structure

* `/api` - Core logic and API endpoints.
* `/core` - Project settings and configuration.
* `/management` - Custom commands (like `load_base_data`).

## 🔑 Environment Variables

Create a `.env` file in the root directory and add:

```env
SECRET_KEY=your-secret-key
```

---

Would you like me to add a section for **API Endpoints** or **Docker** setup to this README?