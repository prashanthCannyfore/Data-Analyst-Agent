import matplotlib.pyplot as plt
import io
import base64
import pandas as pd

def generate_scatterplot(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Scatterplot", regression_line: bool = False) -> str:
    """
    Generates a scatterplot from a DataFrame and returns a Base-64 encoded image data URI.
    Can optionally include a dotted red regression line.
    """
    try:
        plt.style.use('dark_background')  # A clean, dark theme for plots
        plt.figure(figsize=(10, 6))
        
        # Plot scatter points
        plt.scatter(df[x_col], df[y_col], label="Data Points", alpha=0.7)
        
        # Add a regression line if requested
        if regression_line:
            # Calculate linear regression
            m, b = np.polyfit(df[x_col], df[y_col], 1)
            plt.plot(df[x_col], m * df[x_col] + b, color='red', linestyle=':', label='Regression Line')
        
        plt.title(title, color='white')
        plt.xlabel(x_col, color='white')
        plt.ylabel(y_col, color='white')
        plt.grid(True, linestyle='--', alpha=0.5)
        plt.legend()
        
        # Save plot to an in-memory buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close() # Close the plot to free up memory

        # Encode the buffer content to Base-64
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        
        # Return a data URI string
        return f"data:image/png;base64,{image_base64}"
    
    except Exception as e:
        return f"Error generating scatterplot: {e}"