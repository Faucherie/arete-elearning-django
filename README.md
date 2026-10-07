# Arete: eLearning Web Application

Coursework for the University of London BSc Computer Science, Advanced Web Development (CM3035), 2026.

A Django eLearning application where courses are broken into offerings, with separate student, teacher, and administrator permissions. Deployed on AWS EC2 for marking.

- Django and Django REST Framework API
- Real-time chat over WebSockets with Django Channels and Redis
- CSV seeding scripts (`scripts/populate_elearning.py`) and a test suite with factory_boy
- Deployed on Ubuntu (EC2) with restricted SSH, key-based login, and the secret key and database password supplied by environment variables

## Running locally

```bash
python -m venv venv && source venv/bin/activate
pip install django djangorestframework channels channels-redis factory_boy
export DJANGO_SECRET_KEY='any-local-value'
python manage.py migrate
python scripts/populate_elearning.py
python manage.py runserver
```

The full write-up is in `report.pdf`. The seed data is fictional.

---

Scott Swanson
