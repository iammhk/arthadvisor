# ArthAdvisor

ArthAdvisor is a machine learning-based stock recommendation application developed for the FossHack 2024 hackathon. It provides a self-hostable investment platform designed for common investors, offering an easy-to-use interface for stock predictions and portfolio management.

## Features

- Machine learning-based stock predictions using CatBoost
- Daily/weekly stock rankings and recommendations
- User-friendly dashboard for tracking investments
- Backtesting module with performance visualization
- Customizable prediction frequency settings
- Self-hostable platform

## Tech Stack

ArthAdvisor utilizes a modern and efficient tech stack, carefully chosen to provide a robust, scalable, and user-friendly platform. Here's a detailed breakdown of the technologies used and the reasoning behind each choice:

### Backend

- **Python**: A versatile and powerful programming language, ideal for data processing, machine learning, and web development.
  - **Flask**: A lightweight and flexible Python web framework. Flask's simplicity and extensibility make it perfect for building RESTful APIs and serving our web application.

### Frontend

- **Alpine.js**: A lightweight JavaScript framework for adding interactivity to web pages. Its simplicity and small footprint make it ideal for creating responsive user interfaces without the overhead of larger frameworks.
- **Daisy UI**: A plugin for Tailwind CSS that provides a set of pre-designed components. This allows for rapid UI development while maintaining a consistent and professional look.
- **Tailwind CSS**: A utility-first CSS framework that enables quick styling and responsive design. Tailwind's approach allows for highly customizable designs without writing custom CSS.

### Database

- **SQLite**: A lightweight, serverless database engine. SQLite is chosen for its simplicity in setup and maintenance, making it ideal for a self-hostable application. It's perfect for small to medium-scale deployments.

### Machine Learning

- **CatBoost**: An open-source gradient boosting library developed by Yandex. CatBoost is chosen for its high performance, ability to handle categorical features automatically, and resistance to overfitting. These qualities make it well-suited for stock price prediction tasks.

### Data Source

- **yfinance**: A Python library that provides a simple way to download historical market data from Yahoo Finance. It's reliable, easy to use, and provides access to a wide range of financial data needed for stock analysis and prediction.

### Development and Deployment Tools

- **pip**: The package installer for Python, used to manage project dependencies.
- **Git**: For version control and collaborative development.

This tech stack is designed to provide a balance between performance, ease of development, and maintainability. It allows for rapid development and iteration, crucial for a hackathon project, while also providing a solid foundation for potential future scaling and enhancement.

## Prerequisites

- Python 3.9+
- pip

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/marketcalls/arthadvisor.git
   cd arthadvisor
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```


4. Create a `.env` file in the root directory and add the necessary environment variables:
   ```
   SECRET_KEY=your_secret_key
   SQLALCHEMY_DATABASE_URI=sqlite:///arthadvisor.db
   ```

## Running the Application

1. Start the Flask development server:
   ```
   python app.py

   ```

2. Access the application at `http://localhost:5000`

## Automated Data Download and Predictions

This project uses AP Scheduler to automate the periodic download of stock portfolio data and to schedule machine learning trainings and predictions. The initial data download and training/prediction tasks need to be triggered manually, and later they will be scheduled automatically.

### Initial Manual Data Download

To load the stock portfolio data at the start for machine learning trainings and predictions, run the following command:

```bash
python data_downloader.py
```

### Initial Manual Trainings and Predictions

To start the initial machine learning trainings and predictions, run the following command:

```bash
python trainings_predictions.py
```

### Setting Up AP Scheduler for Automated Tasks

1. **Automated Data Download**

   The `data_downloader.py` script is set to be scheduled to download stock portfolio data on a daily basis. AP Scheduler is configured to run this task every 24 hours. To ensure this, the script should be integrated with the main Flask application or run as a standalone script with AP Scheduler enabled.

2. **Automated Trainings and Predictions**

   The `trainings_predictions.py` script is set to be scheduled to run weekly to generate updated predictions. AP Scheduler is configured to run this task every 7 days.

## Usage

1. Register for an account or log in if you already have one.
2. Set your prediction frequency preference in the user settings.
3. View the dashboard to see current stock recommendations and portfolio performance.
4. Use the backtesting module to evaluate the strategy's historical performance.

# ArthAdvisor: Future Roadmap

## Immediate Roadmap Items

### 1. Advanced Portfolio Analytics
- Implement comprehensive risk-adjusted return metrics and sector allocation analysis.
- Provide detailed performance attribution to identify key drivers of portfolio returns.

### 2. Customizable Alerts System
- Develop a flexible alert system for price targets, volatility, and news-based notifications.
- Create a centralized dashboard for managing alerts with multi-channel delivery (mobile, email).

### 3. Intelligent Portfolio Rebalancing
- Implement automated portfolio rebalancing based on user-defined thresholds and strategies.
- Provide smart rebalancing suggestions considering tax implications and market conditions.

### 4. Enhanced Backtesting with Market Scenarios
- Implement portfolio testing against historical market events and user-defined scenarios.
- Provide comparative analysis of portfolio performance against relevant benchmark indices.

### 5. AI-Powered Investment Insights
- Develop NLP-based summarization of key financial news relevant to user portfolios.
- Implement anomaly detection and AI-generated explanations for stock recommendations.

### 6. ML-based Thematic Investing Concepts
- Develop machine learning algorithms to identify and track emerging market themes and trends.
- Provide AI-curated thematic portfolios with regular updates based on market dynamics and user preferences.


### Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](LICENSE) file for details.

### GPL-3.0 License Notice

ArthAdvisor is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

ArthAdvisor is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with ArthAdvisor. If not, see <https://www.gnu.org/licenses/>.

## Acknowledgments

- [Anthropic](https://www.anthropic.com) for Claude 3.5 Sonnet, an AI assistant that helped in project development
- [OpenAI](https://www.openai.com) for ChatGPT-4, which also provided assistance in the development process
- [FossHack 2024](https://fossunited.org/fosshack/2024) organizers and sponsors
- All open-source libraries and tools used in this project
- Amazon SES for email notifications and alerts (free tier)

## Team

- Rajandran - Backend Developer, Database Expert, Creator of OpenAlgo & ArthAdvisor, Lead Maintainer
- Deepanshu - Frontend Engineer , 3rd Year, E.C.E, Thapar Institute of Engineering & Technology, Patiala, Punjab, Contributor
- Aksshaya - Web Designer, Test Engineer and Content Creator, Gopal National School, 7th Grade, Bangalore, Contributor


## Disclaimer

This application is for educational and demonstration purposes only. It does not constitute financial advice. Always conduct your own research and consult with a qualified financial advisor before making investment decisions.
