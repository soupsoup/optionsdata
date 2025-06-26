# Required libraries
import yfinance as yf
import pandas as pd
from flask import Flask, request, render_template_string, Response
from datetime import datetime, timedelta
import os
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Flask app setup
app = Flask(__name__)

# HTML Template for Dashboard
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Options Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; text-align: center; }
        .form-group { margin: 15px 0; }
        label { display: inline-block; width: 120px; font-weight: bold; }
        input[type="text"], select { padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 200px; }
        button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #0056b3; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .error { color: red; background-color: #ffe6e6; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .info { color: #0066cc; background-color: #e6f3ff; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .current-price { font-size: 18px; font-weight: bold; color: #28a745; text-align: center; margin: 10px 0; }
        .heatmap-outer { width: 100vw; margin-left: calc(-1 * ((100vw - 100%) / 2)); background: white; padding: 0; }
        .heatmap-inner { width: 98vw; max-width: 2000px; margin: 0 auto; text-align: center; }
        .gex-chart-container { text-align: center; margin-top: 30px; }
        .gex-chart-container img { 
            width: 800px; 
            max-width: 98vw; 
            height: auto; 
            border: 2px solid #ccc; 
            border-radius: 8px;
            display: block; 
            margin: 0 auto; 
            cursor: zoom-in;
            transition: transform 0.2s ease;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .gex-chart-container img:hover {
            transform: scale(1.02);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .gex-chart-container h3 {
            color: #333;
            font-size: 20px;
            margin-bottom: 15px;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>Options Chain Dashboard for {{ ticker.upper() }}</h2>
        
        {% if current_price %}
        <div class="current-price">Current Price: ${{ current_price }}</div>
        {% endif %}
        
        <form method="get">
            <div class="form-group">
                <label for="ticker">Ticker:</label>
                <input type="text" id="ticker" name="ticker" value="{{ ticker }}" required placeholder="e.g., AAPL, TSLA, SPY">
            </div>
            
            <div class="form-group">
                <label for="expiry">Expiry Date:</label>
                {% if available_expiries %}
                <select id="expiry" name="expiry" required>
                    {% for date in available_expiries %}
                        <option value="{{ date }}" {% if date == expiry %}selected{% endif %}>{{ date }}</option>
                    {% endfor %}
                </select>
                {% else %}
                <select id="expiry" name="expiry" required disabled>
                    <option>No expiry dates available</option>
                </select>
                {% endif %}
            </div>
            
            <div class="form-group">
                <label for="range">Strike Range:</label>
                <input type="text" id="range" name="range" value="{{ strike_range }}" required placeholder="e.g., 150-200">
            </div>
            
            <button type="submit">Get Options Data</button>
        </form>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if info %}
        <div class="info">{{ info }}</div>
        {% endif %}
        
        {% if table %}
        <div style="overflow-x: auto;">
            {{ table|safe }}
        </div>
        {% endif %}
        
        {% if heatmap_img %}
        <div class="heatmap-outer">
            <div class="heatmap-inner">
                <h3 style="margin-top:30px;">Strike Volume Heatmap</h3>
                <img src="data:image/png;base64,{{ heatmap_img }}" style="width:98vw;max-width:2000px;height:auto;border:1px solid #ccc;display:block;margin:0 auto;"/>
            </div>
        </div>
        {% endif %}
        
        {% if table %}
        <div class="gex-chart-container">
            <h3>Options Activity (GEX-style) by Strike</h3>
            <a href="/gex_chart/{{ ticker }}/{{ expiry }}?range={{ strike_range }}" target="_blank">
                <img src="/gex_chart/{{ ticker }}/{{ expiry }}?range={{ strike_range }}" alt="GEX Chart - Click to open in new tab"/>
            </a>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

# Function to get available expiry dates for a ticker
# Only return dates that actually have valid options data

def get_available_expiries(ticker):
    import datetime
    try:
        tk = yf.Ticker(ticker)
        # Try to get all possible expiry dates (from yfinance or fallback)
        expiries = None
        try:
            expiries = tk.options
        except Exception as e:
            print(f"Method 1 failed for {ticker}: {e}")
        if not expiries:
            import time
            time.sleep(1)
            try:
                expiries = tk.options
            except Exception as e:
                print(f"Method 2 failed for {ticker}: {e}")
        if not expiries:
            expiries = get_fallback_expiries(ticker)
        # Validate each expiry by checking if options data exists
        valid_expiries = []
        for date in expiries:
            try:
                opt_chain = tk.option_chain(date)
                if (hasattr(opt_chain, 'calls') and not opt_chain.calls.empty) or (hasattr(opt_chain, 'puts') and not opt_chain.puts.empty):
                    valid_expiries.append(date)
            except Exception as e:
                print(f"Expiry {date} for {ticker} is invalid: {e}")
                continue
        # Sort and limit to 12 dates
        valid_expiries = sorted(valid_expiries)
        return valid_expiries[:12]
    except Exception as e:
        print(f"Error getting expiries for {ticker}: {e}")
        return []

def get_fallback_expiries(ticker):
    """Provide fallback expiry dates when yfinance fails"""
    import datetime
    
    # Generate next 6 months of third Friday dates (typical options expiry)
    today = datetime.date.today()
    fallback_dates = []
    
    for i in range(1, 7):
        # Calculate third Friday of each month
        future_date = today + datetime.timedelta(days=30*i)
        year = future_date.year
        month = future_date.month
        
        # Find third Friday
        first_day = datetime.date(year, month, 1)
        first_friday = first_day + datetime.timedelta(days=(4 - first_day.weekday()) % 7)
        third_friday = first_friday + datetime.timedelta(weeks=2)
        
        # If third Friday has passed, use next month
        if third_friday < today:
            if month == 12:
                year += 1
                month = 1
            else:
                month += 1
            first_day = datetime.date(year, month, 1)
            first_friday = first_day + datetime.timedelta(days=(4 - first_day.weekday()) % 7)
            third_friday = first_friday + datetime.timedelta(weeks=2)
        
        fallback_dates.append(third_friday.strftime('%Y-%m-%d'))
    
    return fallback_dates

# Function to get current stock price
def get_current_price(ticker):
    try:
        tk = yf.Ticker(ticker)
        info = tk.info
        return round(info.get('regularMarketPrice', 0), 2)
    except:
        return None

# Function to fetch and calculate options data
def fetch_options_data(ticker, expiry, strike_min, strike_max):
    tk = yf.Ticker(ticker)
    try:
        opt_chain = tk.option_chain(expiry)
        calls = opt_chain.calls
        puts = opt_chain.puts
    except Exception as e:
        return f"Error fetching data: {e}", None

    if calls.empty and puts.empty:
        return f"No options data available for {ticker} on {expiry}", None

    df = pd.merge(calls, puts, on='strike', how='outer', suffixes=('_call', '_put'))
    df = df[(df['strike'] >= strike_min) & (df['strike'] <= strike_max)].copy()

    if df.empty:
        return f"No options found in strike range {strike_min}-{strike_max} for {ticker}", None

    # Calculate percentages
    df['vC%'] = (df['volume_call'] / (df['volume_call'] + df['volume_put'])) * 100
    df['vP%'] = 100 - df['vC%']
    df['oiC%'] = (df['openInterest_call'] / (df['openInterest_call'] + df['openInterest_put'])) * 100
    df['oiP%'] = 100 - df['oiC%']

    # Select and rename columns for better display
    df = df[['strike', 'volume_call', 'volume_put', 'vC%', 'vP%', 'openInterest_call', 'openInterest_put', 'oiC%', 'oiP%']]
    df.columns = ['Strike', 'Call Vol', 'Put Vol', 'Call Vol %', 'Put Vol %', 'Call OI', 'Put OI', 'Call OI %', 'Put OI %']
    
    df = df.round(1).fillna('-')
    return None, df.to_html(index=False, classes='table')

# Function to generate heatmap image as base64
def generate_heatmap(df):
    if df is None or df.empty:
        return None
    try:
        # Prepare data for heatmap
        heatmap_data = df[['Strike', 'Call Vol', 'Put Vol']].copy()
        heatmap_data = heatmap_data.replace('-', 0)
        heatmap_data['Call Vol'] = pd.to_numeric(heatmap_data['Call Vol'], errors='coerce').fillna(0)
        heatmap_data['Put Vol'] = pd.to_numeric(heatmap_data['Put Vol'], errors='coerce').fillna(0)
        heatmap_data = heatmap_data.set_index('Strike')
        # Create heatmap
        plt.figure(figsize=(min(1.5 * len(heatmap_data), 24), 6))
        sns.heatmap(
            heatmap_data.T,
            cmap='YlOrRd',
            annot=False,
            fmt='.0f',
            cbar=True,
            linewidths=0.5,
            square=False
        )
        plt.title('Call/Put Volume Heatmap by Strike', fontsize=18)
        plt.yticks(rotation=0, fontsize=14)
        plt.xticks(fontsize=12)
        plt.xlabel('Strike', fontsize=16)
        plt.ylabel('', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64
    except Exception as e:
        print(f"Error generating heatmap: {e}")
        return None

# Function to generate GEX-style bar chart as base64
def generate_gex_chart(df, spot_price=None, max_pain=None):
    if df is None or df.empty:
        return None
    try:
        # Use fallback for open interest columns
        if 'Call OI' in df.columns and 'Put OI' in df.columns:
            call_oi = pd.to_numeric(df['Call OI'], errors='coerce').fillna(0)
            put_oi = pd.to_numeric(df['Put OI'], errors='coerce').fillna(0)
            strikes = df['Strike']
        elif 'openInterest_call' in df.columns and 'openInterest_put' in df.columns and 'strike' in df.columns:
            call_oi = pd.to_numeric(df['openInterest_call'], errors='coerce').fillna(0)
            put_oi = pd.to_numeric(df['openInterest_put'], errors='coerce').fillna(0)
            strikes = df['strike']
        else:
            print('No open interest columns found for GEX chart')
            return None
        gex = call_oi - put_oi  # Calls positive, puts negative
        
        # Create larger figure for better magnification
        fig, ax = plt.subplots(figsize=(16, 12), dpi=150)
        
        # Create horizontal bar chart
        bars = ax.barh(strikes, gex, color=["#d62728" if v < 0 else "#2ca02c" for v in gex], alpha=0.7, height=0.8)
        
        # Add zero line
        ax.axvline(0, color='black', linewidth=2)
        
        # Spot price line
        if spot_price:
            ax.axhline(spot_price, color='red', linestyle='--', linewidth=3, label='Spot Price')
            ax.text(ax.get_xlim()[1] * 0.95, spot_price, f'Spot: {spot_price}', 
                   color='red', va='center', ha='right', fontsize=14, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Max Pain line
        if max_pain:
            ax.axhline(max_pain, color='purple', linestyle=':', linewidth=3, label='Max Pain')
            ax.text(ax.get_xlim()[1] * 0.95, max_pain, f'Max Pain: {max_pain}', 
                   color='purple', va='center', ha='right', fontsize=14, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Vol Trigger (closest strike above spot)
        vol_trigger = None
        y_wall = None
        if spot_price is not None and len(strikes) > 0:
            strikes_sorted = sorted(strikes)
            vol_trigger = min([s for s in strikes_sorted if s >= spot_price], default=None)
            y_wall = max([s for s in strikes_sorted if s <= spot_price], default=None)
        
        if vol_trigger:
            ax.axhline(vol_trigger, color='gold', linestyle='-.', linewidth=3, label='Vol Trigger')
            ax.text(ax.get_xlim()[1] * 0.95, vol_trigger, f'Vol Trigger: {vol_trigger}', 
                   color='goldenrod', va='center', ha='right', fontsize=14, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        if y_wall:
            ax.axhline(y_wall, color='blue', linestyle='-', linewidth=3, label='Y Wall')
            ax.text(ax.get_xlim()[1] * 0.95, y_wall, f'Y Wall: {y_wall}', 
                   color='blue', va='center', ha='right', fontsize=14, fontweight='bold',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8))
        
        # Enhanced styling
        ax.set_xlabel('GEX (Call OI - Put OI)', fontsize=16, fontweight='bold')
        ax.set_ylabel('Strike Price', fontsize=16, fontweight='bold')
        ax.set_title('Options Activity (GEX-style) by Strike', fontsize=18, fontweight='bold', pad=20)
        
        # Improve tick labels
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add legend with better positioning
        ax.legend(loc='lower right', fontsize=12, framealpha=0.9)
        
        # Add value labels on bars for better readability
        for i, (bar, value) in enumerate(zip(bars, gex)):
            if abs(value) > max(gex) * 0.05:  # Only label significant bars
                color = 'white' if abs(value) > max(gex) * 0.3 else 'black'
                ax.text(value + (0.02 * max(gex) if value >= 0 else -0.02 * max(gex)), 
                       bar.get_y() + bar.get_height()/2, 
                       f'{int(value):,}', 
                       ha='center' if value >= 0 else 'center',
                       va='center', fontsize=10, fontweight='bold', color=color)
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        return img_base64
    except Exception as e:
        print(f"Error generating GEX chart: {e}")
        return None

@app.route('/', methods=['GET'])
def dashboard():
    ticker = request.args.get('ticker', 'SPY').upper()
    expiry = request.args.get('expiry', '')
    strike_range = request.args.get('range', '')
    
    error = None
    info = None
    table = None
    current_price = None
    available_expiries = []
    heatmap_img = None
    
    # Get available expiries for the ticker (even if empty initially)
    if ticker:
        available_expiries = get_available_expiries(ticker)
        
        if not available_expiries:
            error = f"Unable to fetch options data for {ticker}. This could be due to:\n- Invalid ticker symbol\n- No options available for this stock\n- Temporary API issues\n\nPlease try:\n- Checking the ticker symbol spelling\n- Using a different ticker (e.g., SPY, AAPL, TSLA)\n- Refreshing the page in a few minutes"
        else:
            # Get current price
            current_price = get_current_price(ticker)
            
            # Set default expiry if not provided or if provided expiry is not in available list
            if not expiry or expiry not in available_expiries:
                expiry = available_expiries[0]
            
            # Set default strike range if not provided
            if not strike_range and current_price:
                # Default to ±10% of current price
                min_strike = max(0, current_price * 0.9)
                max_strike = current_price * 1.1
                strike_range = f"{int(min_strike)}-{int(max_strike)}"
            elif not strike_range:
                strike_range = "100-200"  # Generic default
            
            try:
                strike_min, strike_max = map(float, strike_range.split('-'))
                error, table = fetch_options_data(ticker, expiry, strike_min, strike_max)
                
                if not error and table:
                    info = f"Showing options data for {ticker} expiring {expiry} with strikes {strike_min}-{strike_max}"
                    # Get the DataFrame for heatmap
                    _, df_html = fetch_options_data(ticker, expiry, strike_min, strike_max)
                    # Re-fetch as DataFrame for heatmap
                    tk = yf.Ticker(ticker)
                    opt_chain = tk.option_chain(expiry)
                    calls = opt_chain.calls
                    puts = opt_chain.puts
                    df = pd.merge(calls, puts, on='strike', how='outer', suffixes=('_call', '_put'))
                    df = df[(df['strike'] >= strike_min) & (df['strike'] <= strike_max)].copy()
                    if not df.empty:
                        df['Call Vol'] = df['volume_call']
                        df['Put Vol'] = df['volume_put']
                        df['Strike'] = df['strike']
                        heatmap_img = generate_heatmap(df[['Strike', 'Call Vol', 'Put Vol']])
                        # GEX chart is now served from separate endpoint
                        # No need to generate gex_img here
            except ValueError:
                error = "Invalid strike range format. Please use format like '150-200'"
    
    return render_template_string(
        TEMPLATE, 
        ticker=ticker, 
        expiry=expiry, 
        strike_range=strike_range, 
        table=table, 
        error=error, 
        info=info,
        current_price=current_price,
        available_expiries=available_expiries,
        heatmap_img=heatmap_img
    )

# Add a route to serve GEX chart images
@app.route('/gex_chart/<ticker>/<expiry>')
def gex_chart_image(ticker, expiry):
    try:
        # Get parameters from query string
        strike_range = request.args.get('range', '')
        if not strike_range:
            return "Missing strike range parameter", 400
            
        strike_min, strike_max = map(float, strike_range.split('-'))
        
        # Fetch options data
        tk = yf.Ticker(ticker)
        opt_chain = tk.option_chain(expiry)
        calls = opt_chain.calls
        puts = opt_chain.puts
        df = pd.merge(calls, puts, on='strike', how='outer', suffixes=('_call', '_put'))
        df = df[(df['strike'] >= strike_min) & (df['strike'] <= strike_max)].copy()
        
        if df.empty:
            return "No data available", 404
            
        # Prepare data for GEX chart
        df['Call Vol'] = df['volume_call']
        df['Put Vol'] = df['volume_put']
        df['Strike'] = df['strike']
        
        # Get current price
        current_price = get_current_price(ticker)
        
        # Calculate max pain
        if 'openInterest_call' in df.columns and 'openInterest_put' in df.columns:
            max_pain = df.loc[(df['openInterest_call'] - df['openInterest_put']).abs().idxmin(), 'strike']
        else:
            max_pain = None
            
        # Generate GEX chart
        gex_img = generate_gex_chart(df, spot_price=current_price, max_pain=max_pain)
        
        if gex_img:
            # Decode base64 and return as image
            img_data = base64.b64decode(gex_img)
            return Response(img_data, mimetype='image/png')
        else:
            return "Failed to generate chart", 500
            
    except Exception as e:
        return f"Error: {str(e)}", 500

# Run with: flask run (after setting FLASK_APP to this file)
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=True, host='0.0.0.0', port=port)
