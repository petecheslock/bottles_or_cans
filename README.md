# Bottles or Cans

If you like listening to music on headphones, and have read the reviews for them, you'll notice that often times they sound a lot like the reviews for a bottle of wine.  

## Overview
Bottles or Cans is a web application that allows users to submit reviews and vote on their preferences between two categories: headphones and wine. The application features an admin dashboard for managing reviews and users, as well as a user-friendly interface for submitting and viewing reviews.

## Requirements
To set up and run this application, you will need the following:

- Python 3.6 or higher
- Flask
- Flask-SQLAlchemy
- Pandas
- SQLite (or another database of your choice)

You can install the required Python packages using pip. It is recommended to use a virtual environment to manage dependencies.

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/petecheslock/bottles_or_cans.git
   cd bottles_or_cans
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```

4. **Prepare the Database**
   - You can seed the database with reviews by having a `reviews.csv` file in the same directory as the application. This file should contain the initial reviews to be imported into the database. The CSV should have the following columns: `text`, `votes_headphones`, `votes_wine`. If you don't have the file, the database will start empty and you can populate the reviews manually in the web UI.
   - Run the database initialization script to create the necessary tables and import reviews:
   ```bash
   python init_db.py
   ```

## Running the Application
To run the application, execute the following command:

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000/` by default. You can access it through your web browser.

## Admin Access
To access the admin dashboard, login using the admin user during the database initialization.

## Contributing
Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue or submit a pull request.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.