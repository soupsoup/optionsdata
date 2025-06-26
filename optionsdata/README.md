# Options Dashboard

A Flask-based web application for analyzing options chain data with interactive charts and visualizations.

## Features

- **Options Chain Analysis**: View call and put options data with volume and open interest
- **Interactive Heatmaps**: Visualize strike volume patterns
- **GEX Charts**: Gamma Exposure style charts showing options activity by strike
- **Real-time Data**: Powered by Yahoo Finance API
- **Responsive Design**: Works on desktop and mobile devices

## Local Development

### Prerequisites
- Python 3.11+
- pip

### Setup
1. Clone the repository:
```bash
git clone <your-repo-url>
cd optionsdata
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python3 options_dashboard.py
```

5. Open your browser and navigate to `http://localhost:5050`

## Deployment Options

### 1. Heroku (Recommended - Free Tier Available)

#### Prerequisites
- Heroku account
- Heroku CLI installed

#### Deployment Steps
1. Install Heroku CLI and login:
```bash
heroku login
```

2. Create a new Heroku app:
```bash
heroku create your-app-name
```

3. Deploy to Heroku:
```bash
git add .
git commit -m "Initial deployment"
git push heroku main
```

4. Open your app:
```bash
heroku open
```

### 2. Railway (Alternative - Free Tier Available)

#### Prerequisites
- Railway account
- GitHub repository

#### Deployment Steps
1. Connect your GitHub repository to Railway
2. Railway will automatically detect the Python app
3. Deploy with one click
4. Get your live URL

### 3. Render (Alternative - Free Tier Available)

#### Prerequisites
- Render account
- GitHub repository

#### Deployment Steps
1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn options_dashboard:app`
5. Deploy

### 4. DigitalOcean App Platform

#### Prerequisites
- DigitalOcean account
- GitHub repository

#### Deployment Steps
1. Connect your GitHub repository to DigitalOcean
2. Create a new App
3. Select Python as the environment
4. Deploy

### 5. AWS Elastic Beanstalk

#### Prerequisites
- AWS account
- AWS CLI configured

#### Deployment Steps
1. Install AWS EB CLI:
```bash
pip install awsebcli
```

2. Initialize EB application:
```bash
eb init
```

3. Create environment:
```bash
eb create production
```

4. Deploy:
```bash
eb deploy
```

## Environment Variables

For production deployment, you may want to set these environment variables:

- `FLASK_ENV`: Set to `production` for production deployment
- `PORT`: Port number (usually set automatically by hosting platform)

## Project Structure

```
optionsdata/
├── options_dashboard.py    # Main Flask application
├── requirements.txt        # Python dependencies
├── Procfile               # Heroku deployment configuration
├── runtime.txt            # Python version specification
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## API Endpoints

- `GET /`: Main dashboard page
- `GET /gex_chart/<ticker>/<expiry>`: GEX chart image endpoint

## Technologies Used

- **Backend**: Flask, Python
- **Data**: yfinance, pandas
- **Visualization**: matplotlib, seaborn
- **Deployment**: gunicorn, Heroku/Railway/Render

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).

## Support

If you encounter any issues:
1. Check the logs: `heroku logs --tail` (for Heroku)
2. Ensure all dependencies are installed
3. Verify your Python version matches runtime.txt
4. Check that the port is not already in use

## Performance Notes

- The application fetches real-time data from Yahoo Finance
- Chart generation may take a few seconds for large datasets
- Consider implementing caching for better performance in production 