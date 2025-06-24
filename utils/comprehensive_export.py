import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO
import zipfile
import json
from datetime import datetime
from typing import Dict, List, Any
import streamlit as st
import base64

class ComprehensiveExporter:
    """Handles comprehensive export of all reports and analyses"""
    
    def __init__(self, df: pd.DataFrame, demographic_cols: List[str], 
                 targets: Dict[str, float], analysis_results: Dict[str, Any] = None):
        self.df = df
        self.demographic_cols = demographic_cols
        self.targets = targets
        self.analysis_results = analysis_results or {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_comprehensive_package(self) -> bytes:
        """Create a comprehensive ZIP package with all reports and data"""
        
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 1. Executive Summary Report (Excel)
            exec_report = self._create_executive_report()
            zip_file.writestr(f"reports/executive_summary_{self.timestamp}.xlsx", exec_report)
            
            # 2. Raw Data Export (CSV)
            csv_data = self.df.to_csv(index=False)
            zip_file.writestr(f"data/raw_data_{self.timestamp}.csv", csv_data)
            
            # 3. Analysis Summary (JSON)
            analysis_json = self._create_analysis_json()
            zip_file.writestr(f"data/analysis_summary_{self.timestamp}.json", analysis_json)
            
            # 4. Chart Images
            chart_images = self._create_chart_images()
            for chart_name, image_data in chart_images.items():
                zip_file.writestr(f"charts/{chart_name}_{self.timestamp}.png", image_data)
            
            # 5. Detailed Reports
            detailed_reports = self._create_detailed_reports()
            for report_name, report_data in detailed_reports.items():
                zip_file.writestr(f"reports/{report_name}_{self.timestamp}.xlsx", report_data)
            
            # 6. Configuration File
            config_data = self._create_config_file()
            zip_file.writestr(f"config/analysis_config_{self.timestamp}.json", config_data)
            
            # 7. README file
            readme_content = self._create_readme()
            zip_file.writestr("README.txt", readme_content)
        
        zip_buffer.seek(0)
        return zip_buffer.read()
    
    def _create_executive_report(self) -> bytes:
        """Create executive summary Excel report"""
        from utils.export_enhancements import export_comprehensive_report
        
        return export_comprehensive_report(
            self.df, self.demographic_cols, self.targets, self.analysis_results
        )
    
    def _create_analysis_json(self) -> str:
        """Create comprehensive analysis summary as JSON"""
        
        total_people = self.df['TOTAL'].sum()
        
        summary = {
            "analysis_metadata": {
                "timestamp": self.timestamp,
                "total_people": int(total_people),
                "total_modules": self.df['EntityDesc'].nunique(),
                "demographic_columns": self.demographic_cols,
                "targets": self.targets
            },
            "demographic_analysis": {},
            "module_analysis": [],
            "equity_metrics": {}
        }
        
        # Demographic breakdown
        for demo_col in self.demographic_cols:
            if demo_col in self.df.columns:
                actual_count = self.df[demo_col].sum()
                actual_pct = (actual_count / total_people) * 100
                target_pct = self.targets.get(demo_col.lower(), self.targets.get(demo_col, 10))
                gap = actual_pct - target_pct
                
                summary["demographic_analysis"][demo_col] = {
                    "count": int(actual_count),
                    "percentage": round(actual_pct, 2),
                    "target_percentage": target_pct,
                    "gap": round(gap, 2),
                    "status": "on_target" if abs(gap) <= 2 else ("over" if gap > 0 else "under")
                }
        
        # Module analysis
        for entity in self.df['EntityDesc'].unique():
            entity_data = self.df[self.df['EntityDesc'] == entity]
            module_total = entity_data['TOTAL'].sum()
            
            module_info = {
                "module_name": entity,
                "total_people": int(module_total),
                "demographics": {}
            }
            
            for demo_col in self.demographic_cols:
                if demo_col in entity_data.columns:
                    demo_count = entity_data[demo_col].sum()
                    demo_pct = (demo_count / module_total) * 100 if module_total > 0 else 0
                    module_info["demographics"][demo_col] = {
                        "count": int(demo_count),
                        "percentage": round(demo_pct, 2)
                    }
            
            summary["module_analysis"].append(module_info)
        
        # Equity metrics
        on_target = len([d for d in summary["demographic_analysis"].values() if d["status"] == "on_target"])
        total_demographics = len(summary["demographic_analysis"])
        
        summary["equity_metrics"] = {
            "overall_equity_score": round((on_target / total_demographics) * 100, 1) if total_demographics > 0 else 0,
            "demographics_on_target": on_target,
            "total_demographics": total_demographics,
            "largest_gap": max([abs(d["gap"]) for d in summary["demographic_analysis"].values()]) if summary["demographic_analysis"] else 0
        }
        
        return json.dumps(summary, indent=2)
    
    def _create_chart_images(self) -> Dict[str, bytes]:
        """Create PNG images of all charts with robust error handling"""
        
        chart_images = {}
        successful_charts = []
        failed_charts = []
        
        # Chart generation functions with error handling
        chart_generators = [
            ("demographic_heatmap", self._generate_demographic_heatmap),
            ("module_population_bar", self._generate_population_bar),
            ("module_population_heatmap", self._generate_population_heatmap),
            ("module_population_treemap", self._generate_population_treemap),
            ("benchmark_comparison", self._generate_benchmark_chart),
            ("trend_analysis", self._generate_trend_chart),
            ("correlation_heatmap", self._generate_correlation_chart),
        ]
        
        for chart_name, generator_func in chart_generators:
            try:
                chart_data = generator_func()
                if chart_data:
                    chart_images[chart_name] = chart_data
                    successful_charts.append(chart_name)
            except Exception as e:
                failed_charts.append(f"{chart_name}: {str(e)}")
                continue
        
        # Add summary of chart generation
        if successful_charts or failed_charts:
            summary = f"Chart Generation Summary:\n"
            summary += f"Successfully generated: {len(successful_charts)} charts\n"
            if successful_charts:
                summary += f"- {', '.join(successful_charts)}\n"
            if failed_charts:
                summary += f"Failed to generate: {len(failed_charts)} charts\n"
                for failure in failed_charts:
                    summary += f"- {failure}\n"
            
            chart_images["generation_summary"] = summary.encode()
        
        return chart_images
    
    def _generate_demographic_heatmap(self) -> bytes:
        """Generate demographic heatmap chart"""
        from utils.heatmap_fix import create_aligned_heatmap
        fig = create_aligned_heatmap(self.df, self.demographic_cols, self.targets)
        return pio.to_image(fig, format="png", width=1200, height=800)
    
    def _generate_population_bar(self) -> bytes:
        """Generate population bar chart"""
        from utils.module_population_charts import create_module_population_bar_chart
        fig = create_module_population_bar_chart(self.df)
        return pio.to_image(fig, format="png", width=1200, height=600)
    
    def _generate_population_heatmap(self) -> bytes:
        """Generate population heatmap chart"""
        from utils.module_population_charts import create_module_population_heatmap_plotly
        fig = create_module_population_heatmap_plotly(self.df)
        return pio.to_image(fig, format="png", width=1000, height=max(600, len(self.df['EntityDesc'].unique()) * 25))
    
    def _generate_population_treemap(self) -> bytes:
        """Generate population treemap chart"""
        from utils.module_population_charts import create_module_population_treemap
        fig = create_module_population_treemap(self.df)
        return pio.to_image(fig, format="png", width=1000, height=600)
    
    def _generate_benchmark_chart(self) -> bytes:
        """Generate benchmark comparison chart"""
        from utils.advanced_analytics import create_benchmark_comparison_chart
        fig = create_benchmark_comparison_chart(self.df, self.demographic_cols, self.targets)
        return pio.to_image(fig, format="png", width=1000, height=600)
    
    def _generate_trend_chart(self) -> bytes:
        """Generate trend analysis chart"""
        from utils.advanced_analytics import AdvancedDemographicAnalytics
        analytics = AdvancedDemographicAnalytics(self.df, self.demographic_cols)
        fig = analytics.create_trend_analysis_chart()
        return pio.to_image(fig, format="png", width=1200, height=600)
    
    def _generate_correlation_chart(self) -> bytes:
        """Generate correlation heatmap chart"""
        if len(self.demographic_cols) < 2:
            return None
        
        from utils.advanced_analytics import AdvancedDemographicAnalytics
        analytics = AdvancedDemographicAnalytics(self.df, self.demographic_cols)
        fig = analytics.create_correlation_heatmap()
        return pio.to_image(fig, format="png", width=800, height=600)
    
    def _create_detailed_reports(self) -> Dict[str, bytes]:
        """Create detailed analysis reports"""
        
        reports = {}
        
        # Module-by-module detailed report
        module_details = []
        for entity in self.df['EntityDesc'].unique():
            entity_data = self.df[self.df['EntityDesc'] == entity]
            module_total = entity_data['TOTAL'].sum()
            
            module_row = {
                'Module': entity,
                'Total_People': int(module_total),
                'Grade': ', '.join(entity_data['Grade'].unique()) if 'Grade' in entity_data.columns else 'N/A'
            }
            
            # Add demographic percentages
            for demo_col in self.demographic_cols:
                if demo_col in entity_data.columns:
                    demo_count = entity_data[demo_col].sum()
                    demo_pct = (demo_count / module_total) * 100 if module_total > 0 else 0
                    target_pct = self.targets.get(demo_col.lower(), self.targets.get(demo_col, 10))
                    gap = demo_pct - target_pct
                    
                    module_row[f'{demo_col}_Count'] = int(demo_count)
                    module_row[f'{demo_col}_Percentage'] = round(demo_pct, 1)
                    module_row[f'{demo_col}_Gap'] = round(gap, 1)
            
            module_details.append(module_row)
        
        module_df = pd.DataFrame(module_details)
        
        # Create Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            module_df.to_excel(writer, sheet_name='Module Details', index=False)
            
            # Add summary sheet
            summary_data = []
            total_people = self.df['TOTAL'].sum()
            
            for demo_col in self.demographic_cols:
                if demo_col in self.df.columns:
                    actual_count = self.df[demo_col].sum()
                    actual_pct = (actual_count / total_people) * 100
                    target_pct = self.targets.get(demo_col.lower(), self.targets.get(demo_col, 10))
                    gap = actual_pct - target_pct
                    
                    summary_data.append({
                        'Demographic': demo_col,
                        'Total_Count': int(actual_count),
                        'Percentage': round(actual_pct, 1),
                        'Target': target_pct,
                        'Gap': round(gap, 1),
                        'Status': 'On Target' if abs(gap) <= 2 else ('Over' if gap > 0 else 'Under')
                    })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        reports["detailed_analysis"] = output.read()
        
        return reports
    
    def _create_config_file(self) -> str:
        """Create configuration file for the analysis"""
        
        config = {
            "analysis_configuration": {
                "timestamp": self.timestamp,
                "demographic_targets": self.targets,
                "demographic_columns": self.demographic_cols,
                "filters_applied": getattr(self, 'filters_applied', {}),
                "total_records": len(self.df),
                "analysis_version": "1.0"
            },
            "data_summary": {
                "total_people": int(self.df['TOTAL'].sum()),
                "unique_modules": self.df['EntityDesc'].nunique(),
                "unique_grades": self.df['Grade'].nunique() if 'Grade' in self.df.columns else 0,
                "date_range": {
                    "analysis_date": self.timestamp
                }
            }
        }
        
        return json.dumps(config, indent=2)
    
    def _create_readme(self) -> str:
        """Create README file explaining the export package"""
        
        readme = f"""
DEMOGRAPHIC ANALYSIS EXPORT PACKAGE
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

This package contains a comprehensive analysis of demographic representation 
in educational content modules.

PACKAGE CONTENTS:
================

/reports/
- executive_summary_{self.timestamp}.xlsx: Executive summary with key findings
- detailed_analysis_{self.timestamp}.xlsx: Module-by-module breakdown

/data/
- raw_data_{self.timestamp}.csv: Original dataset used for analysis
- analysis_summary_{self.timestamp}.json: Complete analysis results in JSON format

/charts/
- demographic_heatmap_{self.timestamp}.png: Main demographic representation heatmap
- module_population_bar_{self.timestamp}.png: Module population bar chart
- module_population_heatmap_{self.timestamp}.png: Module population density map
- module_population_treemap_{self.timestamp}.png: Proportional module visualization
- benchmark_comparison_{self.timestamp}.png: Actual vs target comparison
- trend_analysis_{self.timestamp}.png: Demographic trends across grades
- correlation_heatmap_{self.timestamp}.png: Demographic correlation matrix

/config/
- analysis_config_{self.timestamp}.json: Analysis parameters and settings

ANALYSIS SUMMARY:
================
Total People Analyzed: {int(self.df['TOTAL'].sum()):,}
Total Modules: {self.df['EntityDesc'].nunique()}
Demographics Tracked: {len(self.demographic_cols)}
Analysis Date: {self.timestamp}

TARGET DEMOGRAPHICS:
===================
"""
        
        for demo, target in self.targets.items():
            readme += f"- {demo}: {target}%\n"
        
        readme += f"""

RECOMMENDATIONS:
===============
Please refer to the executive summary report for detailed recommendations
on improving demographic representation in educational content.

For questions about this analysis, please contact your curriculum development team.
"""
        
        return readme

def create_comprehensive_export_interface(df: pd.DataFrame, demographic_cols: List[str], 
                                        targets: Dict[str, float], analysis_results: Dict[str, Any] = None):
    """Create Streamlit interface for comprehensive export"""
    
    st.subheader("Comprehensive Export Package")
    st.write("Download all reports, charts, and data in one complete package")
    
    if st.button("Generate Complete Export Package", type="primary"):
        with st.spinner("Creating comprehensive export package..."):
            try:
                exporter = ComprehensiveExporter(df, demographic_cols, targets, analysis_results)
                package_data = exporter.create_comprehensive_package()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"demographic_analysis_complete_{timestamp}.zip"
                
                st.download_button(
                    label="Download Complete Package",
                    data=package_data,
                    file_name=filename,
                    mime="application/zip",
                    help="Downloads a ZIP file containing all reports, charts, and data"
                )
                
                st.success("Export package created successfully!")
                
                # Show package contents
                st.info("""
                **Package Contents:**
                - Executive Summary Report (Excel)
                - Detailed Module Analysis (Excel) 
                - Raw Data Export (CSV)
                - Analysis Summary (JSON)
                - All Chart Images (PNG)
                - Configuration Files
                - README Documentation
                """)
                
            except Exception as e:
                st.error(f"Error creating export package: {e}")
    
    st.divider()
    
    # Individual export options
    st.subheader("Individual Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Data Only"):
            csv_data = df.to_csv(index=False)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                label="Download CSV Data",
                data=csv_data,
                file_name=f"demographic_data_{timestamp}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Export Charts Only"):
            with st.spinner("Generating chart package..."):
                try:
                    exporter = ComprehensiveExporter(df, demographic_cols, targets)
                    chart_images = exporter._create_chart_images()
                    
                    if chart_images:
                        # Create ZIP of just charts
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                            for chart_name, image_data in chart_images.items():
                                if chart_name == "generation_summary":
                                    zip_file.writestr(f"chart_generation_log.txt", image_data)
                                else:
                                    zip_file.writestr(f"{chart_name}_{exporter.timestamp}.png", image_data)
                        
                        zip_buffer.seek(0)
                        
                        st.download_button(
                            label="Download Chart Package",
                            data=zip_buffer.read(),
                            file_name=f"demographic_charts_{exporter.timestamp}.zip",
                            mime="application/zip"
                        )
                        
                        # Show generation summary
                        if "generation_summary" in chart_images:
                            summary_text = chart_images["generation_summary"].decode()
                            st.info(summary_text)
                    else:
                        st.warning("No charts could be generated. Please check your data.")
                        
                except Exception as e:
                    st.error(f"Error creating chart package: {e}")
                    st.info("You can still export individual charts by right-clicking on them and selecting 'Download plot as PNG'")
    
    with col3:
        if st.button("Export Summary JSON"):
            try:
                exporter = ComprehensiveExporter(df, demographic_cols, targets, analysis_results)
                json_data = exporter._create_analysis_json()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                st.download_button(
                    label="Download JSON Summary",
                    data=json_data,
                    file_name=f"analysis_summary_{timestamp}.json",
                    mime="application/json"
                )
            except Exception as e:
                st.error(f"Error creating JSON summary: {e}")