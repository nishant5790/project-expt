import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Optional, Union
import logging
from scipy import stats
import warnings

class AdvancedEDA:
    """
    A comprehensive class for Exploratory Data Analysis (EDA) in production environments.
    
    Attributes:
        df (pd.DataFrame): Input DataFrame for analysis
        logger (logging.Logger): Logger instance for tracking operations
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        """
        Initialize the EDA class with input DataFrame.
        
        Args:
            dataframe (pd.DataFrame): Input DataFrame for analysis
        """
        self._validate_input(dataframe)
        self.df = dataframe.copy()
        self._setup_logging()
        
    def _validate_input(self, dataframe: pd.DataFrame) -> None:
        """Validate input DataFrame."""
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Input must be a pandas DataFrame")
        if dataframe.empty:
            raise ValueError("DataFrame cannot be empty")
            
    def _setup_logging(self) -> None:
        """Configure logging for the class."""
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def display_basic_info(self) -> dict:
        """
        Display and return basic information about the DataFrame.
        
        Returns:
            dict: Dictionary containing basic DataFrame statistics
        """
        try:
            info_dict = {
                'shape': self.df.shape,
                'missing_values': self.df.isnull().sum().to_dict(),
                'duplicates': self.df.duplicated().sum(),
                'memory_usage': self.df.memory_usage(deep=True).sum() / 1024**2  # MB
            }
            
            self.logger.info("Basic information analysis completed")
            return info_dict
            
        except Exception as e:
            self.logger.error(f"Error in basic info analysis: {str(e)}")
            raise

    def visualize_distributions(self, 
                              columns: Optional[List[str]] = None,
                              figsize: tuple = (10, 6),
                              save_path: Optional[str] = None) -> None:
        """
        Visualize distributions of numerical and categorical columns.
        
        Args:
            columns: List of column names to visualize
            figsize: Tuple specifying figure size
            save_path: Path to save visualizations
        """
        try:
            columns = columns or self.df.columns
            numerical_cols = self.df[columns].select_dtypes(include=np.number).columns
            categorical_cols = self.df[columns].select_dtypes(include=['object', 'category']).columns
            
            for col in numerical_cols:
                plt.figure(figsize=figsize)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    sns.histplot(self.df[col].dropna(), kde=True)
                    plt.title(f'Distribution of {col}')
                    plt.xlabel(col)
                    plt.ylabel('Frequency')
                    
                    if save_path:
                        plt.savefig(f"{save_path}/{col}_distribution.png")
                    plt.close()
            
            for col in categorical_cols:
                plt.figure(figsize=figsize)
                value_counts = self.df[col].value_counts()
                if len(value_counts) > 50:
                    self.logger.warning(f"Column {col} has too many unique values (>{50})")
                    continue
                    
                sns.countplot(y=self.df[col].dropna(), order=value_counts.index)
                plt.title(f'Count of {col}')
                plt.xlabel('Count')
                plt.ylabel(col)
                
                if save_path:
                    plt.savefig(f"{save_path}/{col}_counts.png")
                plt.close()
                
        except Exception as e:
            self.logger.error(f"Error in distribution visualization: {str(e)}")
            raise

    def analyze_correlations(self, 
                           method: str = 'pearson',
                           threshold: float = 0.5) -> pd.DataFrame:
        """
        Analyze and visualize correlations between numerical variables.
        
        Args:
            method: Correlation method ('pearson', 'spearman', or 'kendall')
            threshold: Correlation threshold for highlighting
            
        Returns:
            pd.DataFrame: Correlation matrix
        """
        try:
            numerical_cols = self.df.select_dtypes(include=np.number).columns
            corr_matrix = self.df[numerical_cols].corr(method=method)
            
            plt.figure(figsize=(12, 8))
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
            plt.title(f'{method.capitalize()} Correlation Matrix')
            plt.tight_layout()
            
            # Filter significant correlations
            significant_corr = corr_matrix.unstack()
            significant_corr = significant_corr[abs(significant_corr) > threshold]
            significant_corr = significant_corr[significant_corr != 1.0]
            
            self.logger.info(f"Found {len(significant_corr)} significant correlations")
            return corr_matrix
            
        except Exception as e:
            self.logger.error(f"Error in correlation analysis: {str(e)}")
            raise

    def detect_outliers(self, 
                       columns: Optional[List[str]] = None,
                       method: str = 'zscore',
                       threshold: float = 3.0) -> dict:
        """
        Detect outliers in numerical columns.
        
        Args:
            columns: List of columns to analyze
            method: Method for outlier detection ('zscore' or 'iqr')
            threshold: Threshold for outlier detection
            
        Returns:
            dict: Dictionary containing outlier information for each column
        """
        try:
            columns = columns or self.df.select_dtypes(include=np.number).columns
            outliers_dict = {}
            
            for col in columns:
                if method == 'zscore':
                    z_scores = np.abs(stats.zscore(self.df[col].dropna()))
                    outliers = (z_scores > threshold).sum()
                else:  # IQR method
                    Q1 = self.df[col].quantile(0.25)
                    Q3 = self.df[col].quantile(0.75)
                    IQR = Q3 - Q1
                    outliers = ((self.df[col] < (Q1 - 1.5 * IQR)) | 
                              (self.df[col] > (Q3 + 1.5 * IQR))).sum()
                
                outliers_dict[col] = {
                    'count': outliers,
                    'percentage': (outliers / len(self.df)) * 100
                }
            
            return outliers_dict
            
        except Exception as e:
            self.logger.error(f"Error in outlier detection: {str(e)}")
            raise