import threading
import time
from bots.chart_bot import analyze_and_plot
from bots.rl_bot import run_simulation
from web.dashboard import app as dashboard_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def run_rl_once():
    """
    Run the RL simulation for a fixed number of episodes.
    """
    print("Starting RL simulation...")
    trainer = run_simulation(episodes=3)  # You can adjust the number of episodes
    print("RL simulation done. Q-table size:", len(trainer.q))


def generate_chart_once():
    """
    Generate the final chart and recommendation once.
    """
    print("Generating chart...")
    chart_path, recommendation = analyze_and_plot()
    print("Chart saved at:", chart_path)
    print("Recommendation:", recommendation)


def start_dashboard():
    """
    Start the Flask dashboard.
    """
    dashboard_app.run(port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":
    # Step 1: Run RL simulation
    run_rl_once()

    # Step 2: Generate the chart once
    generate_chart_once()

    # Step 3: Start the Flask dashboard in a separate thread
    t = threading.Thread(target=start_dashboard, daemon=True)
    t.start()
    print("Dashboard running at http://127.0.0.1:5000")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
