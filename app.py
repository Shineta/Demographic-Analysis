import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import os
from utils.data_processor import DataProcessor
from utils.visualizations import create_heatmap, create_module_summary_chart
from utils.export_utils import export_to_excel, export_heatmap_data
# Database import with graceful handling
try:
    from utils.database import DatabaseManager
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False
import io

# Block all social media previews and crawlers
# components.html("""
# <head>
#     <meta name="robots" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="googlebot" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="bingbot" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="slurp" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="facebookexternalhit" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="twitterbot" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="linkedinbot" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="discordbot" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="whatsappbot" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta name="telegrambot" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
#     <meta property="og:image" content="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">
#     <meta property="og:image:width" content="1">
#     <meta property="og:image:height" content="1">
#     <meta property="og:title" content="Access Restricted">
#     <meta property="og:description" content="This content is not available for preview">
#     <meta property="og:type" content="website">
#     <meta name="twitter:card" content="summary">
#     <meta name="twitter:image" content="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">
#     <meta name="twitter:title" content="Access Restricted">
#     <meta name="twitter:description" content="This content is not available for preview">
#     <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate, max-age=0">
#     <meta http-equiv="Pragma" content="no-cache">
#     <meta http-equiv="Expires" content="Thu, 01 Jan 1970 00:00:00 GMT">
# </head>
# """, height=0)

# Remove the existing components.html() block completely and replace st.set_page_config with:

st.set_page_config(page_title="Demographic Analysis Tool",
                   page_icon="📊",
                   layout="wide",
                   initial_sidebar_state="expanded",
                   menu_items={
                       'Get Help': None,
                       'Report a bug': None,
                       'About': None
                   })

# Add this immediately after st.set_page_config to inject custom meta tags
st.markdown("""
<head>
    <meta name="robots" content="noindex, nofollow, nosnippet, noarchive, noimageindex">
    <meta property="og:image" content="">
    <meta property="og:title" content="">
    <meta property="og:description" content="">
    <meta name="twitter:card" content="">
    <meta name="twitter:image" content="">
    <meta name="twitter:title" content="">
    <meta name="twitter:description" content="">
</head>
""",
            unsafe_allow_html=True)

# Configure page
st.set_page_config(page_title="Demographic Analysis Tool",
                   page_icon="📊",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Handle root path routing for custom domain
if st.query_params.get("app") is None and "replit" not in st.session_state.get(
        "url", ""):
    st.query_params["app"] = "true"

# Initialize database
if DATABASE_URL := os.getenv('DATABASE_URL'):
    try:
        if DB_AVAILABLE:
            db_manager = DatabaseManager()
            db_manager.init_db()
            st.session_state.db_available = True
            st.session_state.db_manager = db_manager
        else:
            st.session_state.db_available = False
    except Exception as e:
        st.session_state.db_available = False
else:
    st.session_state.db_available = False

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = None
if 'current_dataset_id' not in st.session_state:
    st.session_state.current_dataset_id = None
if 'dataset_source' not in st.session_state:
    st.session_state.dataset_source = 'upload'  # 'upload' or 'database'

# Main title
st.title("📊 Demographic Analysis Tool")
st.markdown(
    "Upload educational content data to analyze demographic representation and module totals"
)

# Sidebar for data management
with st.sidebar:
    st.header("📊 Data Source")

    # Data source selection - only show database option if available
    if st.session_state.get('db_available', False):
        data_source = st.radio("Choose data source:",
                               ["Upload New File", "Load from Database"],
                               key="data_source_radio")
    else:
        data_source = "Upload New File"
        if not st.session_state.get('db_available',
                                    False) and not st.session_state.get(
                                        'info_shown', False):
            st.info(
                "Memory-only mode - uploaded data won't be saved between sessions"
            )
            st.session_state.info_shown = True

    if data_source == "Upload New File":
        st.session_state.dataset_source = 'upload'
        uploaded_file = st.file_uploader(
            "Upload Excel file (.xlsx)",
            type=['xlsx'],
            help=
            "File should contain columns: Grade, EntityDesc, Component Desc, demographic fields (AAM, AAF, PCM, LGBTF, OTHER_M, etc.), and TOTAL"
        )
    else:
        st.session_state.dataset_source = 'database'
        uploaded_file = None

        # Load datasets from database
        db_manager = st.session_state.get('db_manager')
        if db_manager:
            datasets = db_manager.get_datasets()
        else:
            datasets = []
        if datasets:
            dataset_options = {
                f"{d['name']} ({d['rows_count']} rows)": d['id']
                for d in datasets
            }
            selected_dataset = st.selectbox("Select dataset:",
                                            options=list(
                                                dataset_options.keys()),
                                            key="dataset_selector")

            if selected_dataset and st.button("Load Dataset"):
                dataset_id = dataset_options[selected_dataset]
                try:
                    df = db_manager.load_dataset_data(dataset_id)
                    st.session_state.data_processor = DataProcessor(df)
                    st.session_state.data = df
                    st.session_state.current_dataset_id = dataset_id
                    st.success(f"Loaded dataset with {len(df)} rows")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading dataset: {e}")
        else:
            st.info(
                "No datasets found in database. Upload a file first to save it."
            )

    if uploaded_file is not None:
        try:
            # First, load the file to show column preview
            with st.spinner("Loading file..."):
                df_preview = pd.read_excel(uploaded_file)

            # Show file preview before validation
            st.subheader("📋 File Preview")
            st.write(f"**Rows:** {len(df_preview)}")
            st.write(f"**Columns:** {len(df_preview.columns)}")

            # Show available columns
            with st.expander("📋 Available Columns", expanded=True):
                cols_display = st.columns(3)
                for i, col in enumerate(df_preview.columns):
                    with cols_display[i % 3]:
                        st.write(f"• {col}")

            # Show first few rows
            with st.expander("📊 Data Sample"):
                st.dataframe(df_preview.head(), use_container_width=True)

            # Now try to process with validation
            with st.spinner("Validating and processing data..."):
                st.session_state.data_processor = DataProcessor(df_preview)
                st.session_state.data = df_preview
                st.session_state.current_dataset_id = None  # Reset for new upload

            st.success(
                f"✅ Successfully loaded and validated {len(df_preview)} rows of data"
            )

            # Option to save to database - only if database is available
            if st.session_state.get('db_available', False):
                with st.expander("💾 Save to Database"):
                    dataset_name = st.text_input(
                        "Dataset name:",
                        value=uploaded_file.name.split('.')[0],
                        key="save_name")
                    dataset_description = st.text_area(
                        "Description (optional):", key="save_desc")

                    if st.button("Save Dataset",
                                 key="save_dataset",
                                 type="primary"):
                        try:
                            dataset_id = db_manager.save_dataset(
                                df_preview, uploaded_file.name, dataset_name,
                                dataset_description)
                            st.session_state.current_dataset_id = dataset_id
                            st.success(
                                f"Dataset saved successfully with ID: {dataset_id}"
                            )
                        except Exception as e:
                            st.error(f"Error saving dataset: {e}")

        except Exception as e:
            error_msg = str(e)
            st.error(f"❌ Error loading file:")

            # Display detailed error information in an expandable section
            with st.expander("View Error Details", expanded=True):
                st.code(error_msg, language=None)

            # Show column mapping help
            if "Could not find required columns" in error_msg:
                st.info(
                    "💡 **Column Mapping Help**: The tool looks for columns with these names or similar variations:"
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    **Grade/Level**: grade, level, grade level, gradelevel
                    **Module/Entity**: entity, module, lesson, title, content
                    """)
                with col2:
                    st.markdown("""
                    **Component**: component, activity, activity type
                    **Total Count**: total, people, count, sum
                    """)

                st.markdown(
                    "Try renaming your columns to match these patterns, or ensure your data contains these types of information."
                )

            st.session_state.data = None
            st.session_state.data_processor = None

# Main content area
if st.session_state.data is not None and st.session_state.data_processor is not None:
    processor = st.session_state.data_processor

    # Filters section
    st.header("Filters")

    # Create filter layout similar to the image
    filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 3])

    with filter_col1:
        st.subheader("Grade")
        grades = processor.get_unique_values('Grade')

        # Create buttons for each grade
        grade_cols = st.columns(min(len(grades), 4))
        selected_grades = []

        for i, grade in enumerate(grades):
            with grade_cols[i % 4]:
                if st.checkbox(grade, value=True, key=f"grade_{grade}"):
                    selected_grades.append(grade)

    with filter_col2:
        st.subheader("Component")
        components = processor.get_unique_values('Component Desc')

        # Create buttons for each component
        comp_cols = st.columns(min(len(components), 3))
        selected_components = []

        for i, comp in enumerate(components):
            with comp_cols[i % 3]:
                comp_short = comp[:10] + "..." if len(comp) > 10 else comp
                if st.checkbox(comp_short,
                               value=True,
                               key=f"comp_{i}",
                               help=comp):
                    selected_components.append(comp)

    with filter_col3:
        st.subheader("Select Entity Descriptions")
        from utils.module_validator import validate_modules_with_demographic_data, create_enhanced_module_options, get_actual_module_name, check_module_has_data

        # Validate modules and create enhanced options
        modules_status = validate_modules_with_demographic_data(processor)
        entity_options = create_enhanced_module_options(modules_status)

        selected_entity = st.selectbox(
            "Choose Module:",
            options=entity_options,
            key="entity_select",
            help=
            f"✓ = Has demographic data ({len(modules_status['with_data'])} modules)\n(no data) = No demographic data ({len(modules_status['without_data'])} modules)"
        )

        # Show module status summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Modules with Data", len(modules_status['with_data']))
        with col2:
            st.metric("Modules without Data",
                      len(modules_status['without_data']))

        # Process selection and warn if no data module selected
        if selected_entity == "All Modules":
            entities = processor.get_unique_values('EntityDesc')
            selected_entities = entities
        else:
            actual_entity = get_actual_module_name(selected_entity)
            selected_entities = [actual_entity]

            if not check_module_has_data(selected_entity):
                st.warning(
                    f"⚠️ Selected module '{actual_entity}' has no demographic data. Heat map may be empty."
                )
            else:
                st.success(
                    f"✅ Selected module '{actual_entity}' has demographic data available."
                )

    # Demographics filter
    st.subheader("Demographics")
    demographic_cols = processor.get_demographic_columns()
    if demographic_cols:
        demo_cols = st.columns(min(len(demographic_cols), 6))
        selected_demographics = []

        for i, demo in enumerate(demographic_cols):
            with demo_cols[i % 6]:
                if st.checkbox(demo, value=True, key=f"demo_{demo}"):
                    selected_demographics.append(demo)
    else:
        selected_demographics = []

    # Apply filters and get processed data
    if selected_grades and selected_components and selected_entities:
        filters = {
            'Grade': selected_grades,
            'Component Desc': selected_components,
            'EntityDesc': selected_entities
        }

        # Apply filters properly to ensure data is actually filtered
        filtered_data = processor.apply_filters(filters)

        # Additional filtering for single module selection
        if selected_entity != "All Modules":
            # Clean the entity name (remove indicators)
            clean_entity_name = selected_entity.replace(" ✓", "").replace(
                " (no data)", "")
            # Ensure we're only getting data for the selected module
            filtered_data = filtered_data[filtered_data['EntityDesc'] ==
                                          clean_entity_name]
        st.session_state.processed_data = filtered_data

        if len(filtered_data) > 0:
            st.divider()

            # Heat Map Section
            st.header("Demographic Heat Map")

            # Get filtered demographic columns
            if selected_demographics:
                demographic_cols = selected_demographics
            else:
                demographic_cols = processor.get_demographic_columns()

            if demographic_cols:
                # Configurable target demographics with improved UI
                with st.expander(
                        "Configure Demographic Targets (Equity-Driven Defaults)",
                        expanded=False):
                    st.info(
                        "These targets are based on demographic equity goals. Adjust as needed for your specific context."
                    )

                    target_col1, target_col2 = st.columns(2)
                    target_demographics = {}

                    # Get smart default targets based on demographic equity goals
                    default_targets = processor.get_default_demographic_targets(
                    )

                    # Show summary of current demographics found
                    st.write(
                        f"**Found {len(demographic_cols)} demographic columns:** {', '.join(demographic_cols[:5])}"
                    )
                    if len(demographic_cols) > 5:
                        st.write(f"...and {len(demographic_cols) - 5} more")

                    for i, demo_col in enumerate(demographic_cols):
                        with target_col1 if i % 2 == 0 else target_col2:
                            # Get smart default value for this demographic
                            demo_lower = demo_col.lower()
                            default_value = (default_targets.get(demo_lower)
                                             or default_targets.get(demo_col)
                                             or 10.0)

                            target_demographics[demo_col] = st.number_input(
                                f"{demo_col} Target %",
                                min_value=0.0,
                                max_value=100.0,
                                value=default_value,
                                step=0.5,
                                key=f"target_{demo_col}",
                                help=
                                f"Equity-driven default: {default_value}%. This represents the desired representation percentage for this demographic group."
                            )

                # Check if filtered data has demographic data
                total_demo_data = sum(filtered_data[col].sum()
                                      for col in demographic_cols
                                      if col in filtered_data.columns)

                # Show filtering status with better formatting
                if selected_entity == "All Modules":
                    st.info(
                        f"📊 Analysis includes {filtered_data['EntityDesc'].nunique()} modules with {len(filtered_data)} total rows"
                    )
                else:
                    clean_name = selected_entity.replace(" ✓", "").replace(
                        " (no data)", "")
                    status_icon = "🎯" if " ✓" in selected_entity else "⚠️"
                    st.info(
                        f"{status_icon} Focused analysis on: **{clean_name}** ({len(filtered_data)} rows)"
                    )

                if total_demo_data == 0:
                    st.error("🚫 No demographic data found in filtered results")

                    # Run quick diagnostic
                    st.write("**Possible causes:**")
                    st.write("• Selected modules have no demographic data")
                    st.write("• Demographic columns not detected properly")
                    st.write("• Data filtering is too restrictive")

                    # Show available data for debugging
                    with st.expander("🔍 Diagnostic Information"):
                        st.write("**Available columns:**",
                                 list(filtered_data.columns))
                        st.write("**Detected demographic columns:**",
                                 demographic_cols)
                        st.write("**Sample data:**")
                        st.dataframe(filtered_data.head(3))
                else:
                    # Create improved heatmap with proper filtering
                    from utils.heatmap_fix import create_aligned_heatmap
                    heatmap_fig = create_aligned_heatmap(
                        filtered_data, demographic_cols, target_demographics)
                    st.plotly_chart(heatmap_fig,
                                    use_container_width=True,
                                    key="main_heatmap")

                    st.divider()

                    # Population Distribution Section
                    st.subheader("👥 Population Distribution Analysis")

                    # Create tabs for population analysis
                    pop_dist_tab1, pop_dist_tab2, pop_dist_tab3 = st.tabs([
                        "🔥 Grade vs Module Heatmap", "📊 Grade Summary",
                        "📈 Module Summary"
                    ])

                    with pop_dist_tab1:
                        st.write(
                            "**Population distribution across grades and modules**"
                        )

                        # Controls for customization
                        col1, col2 = st.columns(2)
                        with col1:
                            swap_axes = st.checkbox(
                                "Switch Axes (Module vs Grade)",
                                key="pop_swap_axes")
                        with col2:
                            color_scheme = st.selectbox("Color Scheme:", [
                                "Blues", "Viridis", "Plasma", "Inferno",
                                "Cividis", "Turbo", "RdYlBu", "Spectral"
                            ],
                                                        key="pop_color_scheme")

                        from utils.population_heatmap import create_population_heatmap
                        pop_heatmap_fig = create_population_heatmap(
                            filtered_data, swap_axes, color_scheme)
                        st.plotly_chart(pop_heatmap_fig,
                                        use_container_width=True)

                    with pop_dist_tab2:
                        st.write("**Total people by grade level**")
                        from utils.population_heatmap import create_grade_summary_chart
                        grade_summary_fig = create_grade_summary_chart(
                            filtered_data)
                        st.plotly_chart(grade_summary_fig,
                                        use_container_width=True)

                    with pop_dist_tab3:
                        st.write("**Total people by module**")
                        from utils.population_heatmap import create_module_summary_chart
                        module_summary_fig = create_module_summary_chart(
                            filtered_data)
                        st.plotly_chart(module_summary_fig,
                                        use_container_width=True)

                    st.divider()

                    # Module Population Analysis Section
                    st.header("📊 Module Population Analysis")

                    from utils.module_population_charts import (
                        create_module_population_bar_chart,
                        create_module_population_heatmap_table,
                        create_module_population_heatmap_plotly,
                        create_module_population_treemap,
                        create_population_distribution_chart,
                        get_population_statistics)

                    # Population statistics
                    pop_stats = get_population_statistics(filtered_data)
                    if 'error' not in pop_stats:
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Modules",
                                      pop_stats['total_modules'])
                        with col2:
                            st.metric("Total People",
                                      f"{pop_stats['total_people']:,}")
                        with col3:
                            st.metric(
                                "Avg per Module",
                                f"{pop_stats['avg_people_per_module']:,.1f}")
                        with col4:
                            st.metric(
                                "Median Population",
                                f"{pop_stats['median_population']:,.1f}")

                        # Largest and smallest modules
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(
                                f"**Largest Module:** {pop_stats['largest_module']['name']} ({pop_stats['largest_module']['count']:,} people)"
                            )
                        with col2:
                            st.info(
                                f"**Smallest Module:** {pop_stats['smallest_module']['name']} ({pop_stats['smallest_module']['count']:,} people)"
                            )

                    # View mode selection
                    view_mode = st.radio("Choose visualization:", [
                        "Bar Chart", "Population Heatmap", "Treemap",
                        "Heat Map Table", "Distribution Pie Chart"
                    ],
                                         horizontal=True,
                                         key="population_view_mode")

                    if view_mode == "Bar Chart":
                        bar_fig = create_module_population_bar_chart(
                            filtered_data)
                        st.plotly_chart(bar_fig,
                                        use_container_width=True,
                                        key="population_bar")
                    elif view_mode == "Population Heatmap":
                        heatmap_fig = create_module_population_heatmap_plotly(
                            filtered_data)
                        st.plotly_chart(heatmap_fig,
                                        use_container_width=True,
                                        key="population_heatmap")
                        st.info(
                            "Colors represent population density: Yellow (low) to Red (high)"
                        )
                    elif view_mode == "Treemap":
                        treemap_fig = create_module_population_treemap(
                            filtered_data)
                        st.plotly_chart(treemap_fig,
                                        use_container_width=True,
                                        key="population_treemap")
                        st.info(
                            "Rectangle size represents population count - larger rectangles = more people"
                        )
                    elif view_mode == "Heat Map Table":
                        heatmap_table = create_module_population_heatmap_table(
                            filtered_data)
                        if not heatmap_table.empty and 'Message' not in heatmap_table.columns:
                            st.dataframe(heatmap_table,
                                         use_container_width=True,
                                         hide_index=True)
                        else:
                            st.warning(
                                "No population data available for heat map table"
                            )
                    else:  # Distribution Pie Chart
                        pie_fig = create_population_distribution_chart(
                            filtered_data)
                        st.plotly_chart(pie_fig,
                                        use_container_width=True,
                                        key="population_pie")

                    # Add heatmap controls
                    with st.expander("🎛️ Heat Map Controls", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            show_zero_filter = st.checkbox(
                                "Hide Zero Demographics",
                                value=False,
                                key="hide_zero_demo")
                            if show_zero_filter:
                                # Filter out demographics with zero values across all filtered data
                                non_zero_demographics = []
                                for demo_col in demographic_cols:
                                    if demo_col in filtered_data.columns and filtered_data[
                                            demo_col].sum() > 0:
                                        non_zero_demographics.append(demo_col)

                                if non_zero_demographics:
                                    st.write(
                                        f"Showing {len(non_zero_demographics)} demographics with data"
                                    )
                                    heatmap_fig_filtered = create_improved_heatmap(
                                        filtered_data, non_zero_demographics,
                                        target_demographics)
                                    st.plotly_chart(heatmap_fig_filtered,
                                                    use_container_width=True,
                                                    key="filtered_heatmap")
                                else:
                                    st.warning(
                                        "No demographics have data in the current selection"
                                    )

                        with col2:
                            sort_option = st.selectbox("Sort modules by:", [
                                "Default", "Largest Gap", "Smallest Gap",
                                "Total People", "Module Name"
                            ],
                                                       key="sort_modules")
                            if sort_option != "Default":
                                st.info(
                                    f"Sorting by {sort_option} - feature coming soon!"
                                )

                        with col3:
                            if st.button("Download Heat Map",
                                         key="download_heatmap"):
                                st.info(
                                    "Right-click on the heat map and select 'Download plot as a png' to save the visualization."
                                )
                    st.divider()

                    # Advanced Analytics Section
                    st.header("Advanced Analytics")

                    from utils.advanced_analytics import AdvancedDemographicAnalytics, create_benchmark_comparison_chart

                    analytics = AdvancedDemographicAnalytics(
                        filtered_data, demographic_cols)

                    # Analytics tabs
                    tab1, tab2, tab3, tab4 = st.tabs([
                        "Equity Scorecard", "Gap Analysis", "Trends",
                        "Correlations"
                    ])

                    with tab1:
                        # Equity Scorecard
                        scorecard = analytics.generate_equity_scorecard(
                            target_demographics)

                        col1, col2 = st.columns([1, 2])
                        with col1:
                            overall_score = scorecard['overall_score']
                            score_color = "normal" if overall_score >= 80 else "inverse" if overall_score >= 60 else "off"
                            st.metric("Overall Equity Score",
                                      f"{overall_score:.0f}/100",
                                      delta_color=score_color)

                            # Score interpretation
                            if overall_score >= 90:
                                st.success("Excellent equity performance")
                            elif overall_score >= 70:
                                st.info(
                                    "Good equity with room for improvement")
                            else:
                                st.warning("Significant equity gaps detected")

                        with col2:
                            # Benchmark comparison
                            benchmark_fig = create_benchmark_comparison_chart(
                                filtered_data, demographic_cols,
                                target_demographics)
                            st.plotly_chart(benchmark_fig,
                                            use_container_width=True)

                        # Recommendations
                        if scorecard['recommendations']:
                            st.subheader("Recommendations")
                            for rec in scorecard['recommendations']:
                                st.write(f"• {rec}")

                    with tab2:
                        # Gap Analysis
                        gap_analysis = analytics.detect_representation_gaps(
                            target_demographics)
                        if not gap_analysis.empty:
                            st.subheader(
                                "Modules with Largest Representation Gaps")
                            st.dataframe(gap_analysis,
                                         use_container_width=True,
                                         hide_index=True)

                            # Highlight high-risk modules
                            high_risk = gap_analysis[gap_analysis['Gap_Range']
                                                     > 30]
                            if not high_risk.empty:
                                st.warning(
                                    f"{len(high_risk)} modules have representation gaps >30 percentage points"
                                )
                        else:
                            st.info(
                                "No significant representation gaps detected")

                    with tab3:
                        # Trend Analysis
                        trend_fig = analytics.create_trend_analysis_chart()
                        st.plotly_chart(trend_fig, use_container_width=True)

                    with tab4:
                        # Correlation Analysis
                        if len(demographic_cols) >= 2:
                            corr_fig = analytics.create_correlation_heatmap()
                            st.plotly_chart(corr_fig, use_container_width=True)
                            st.info(
                                "Correlation analysis shows relationships between different demographic groups"
                            )
                        else:
                            st.info(
                                "Need at least 2 demographic columns for correlation analysis"
                            )

                    st.divider()

                    # AI Curriculum Content Advisor Section
                    st.header("🤖 AI Curriculum Content Advisor")

                    from utils.demographic_chatbot import create_chatbot_interface

                    create_chatbot_interface(filtered_data, demographic_cols,
                                             target_demographics)

                    st.divider()

                    # Enhanced Export Section
                    st.header("📊 Export & Reports")

                    from utils.comprehensive_export import create_comprehensive_export_interface
                    from utils.export_enhancements import export_comprehensive_report, create_download_button
                    from datetime import datetime

                    # Comprehensive export interface
                    create_comprehensive_export_interface(
                        filtered_data, demographic_cols, target_demographics, {
                            'scorecard': scorecard,
                            'gap_analysis': gap_analysis
                        })

                    st.divider()

                    # Quick export options
                    st.subheader("Quick Export Options")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("Generate Executive Report",
                                     type="secondary"):
                            with st.spinner("Generating executive report..."):
                                report_data = export_comprehensive_report(
                                    filtered_data, demographic_cols,
                                    target_demographics, {
                                        'scorecard': scorecard,
                                        'gap_analysis': gap_analysis
                                    })
                                create_download_button(
                                    report_data, "demographic_analysis_report",
                                    "Download Executive Report")

                    with col2:
                        if st.button("Export Current Data"):
                            csv_data = filtered_data.to_csv(index=False)
                            timestamp = datetime.now().strftime(
                                "%Y%m%d_%H%M%S")
                            st.download_button(
                                label="Download Filtered Data",
                                data=csv_data,
                                file_name=
                                f"filtered_demographic_data_{timestamp}.csv",
                                mime="text/csv")

                    with col3:
                        if st.button("Save Analysis Session"):
                            if st.session_state.get('db_available', False):
                                try:
                                    session_name = f"Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                    st.success(
                                        "Analysis session saved to database")
                                except Exception as e:
                                    st.error(f"Error saving session: {e}")
                            else:
                                st.info(
                                    "Database not available for session saving"
                                )
            else:
                st.warning("No demographic columns found in the dataset")

            st.divider()

            # Module Summary Table Section
            st.header("Module Summary Table")

            # Calculate module totals
            module_totals = processor.calculate_module_totals(filtered_data)

            if not module_totals.empty:
                # Create a clean table display
                display_df = module_totals.copy()
                display_df.columns = ['Module', 'Grade', 'Total People']

                # Add component information
                component_info = []
                for _, row in display_df.iterrows():
                    entity_data = filtered_data[filtered_data['EntityDesc'] ==
                                                row['Module']]
                    components = entity_data['Component Desc'].unique()
                    component_info.append(components[0] if len(components) ==
                                          1 else "Multiple")

                display_df.insert(2, 'Component', component_info)

                # Display the table
                st.dataframe(display_df,
                             use_container_width=True,
                             hide_index=True,
                             column_config={
                                 "Module":
                                 st.column_config.TextColumn("Module",
                                                             width="large"),
                                 "Grade":
                                 st.column_config.TextColumn("Grade",
                                                             width="small"),
                                 "Component":
                                 st.column_config.TextColumn("Component",
                                                             width="medium"),
                                 "Total People":
                                 st.column_config.NumberColumn("Total People",
                                                               width="medium",
                                                               format="%d")
                             })

                # Summary metrics
                total_people = display_df['Total People'].sum()
                total_modules = len(display_df)

                metric_col1, metric_col2, metric_col3 = st.columns(3)
                with metric_col1:
                    st.metric("Total Modules", total_modules)
                with metric_col2:
                    st.metric("Total People", f"{total_people:,}")
                with metric_col3:
                    avg_per_module = total_people / total_modules if total_modules > 0 else 0
                    st.metric("Avg People/Module", f"{avg_per_module:.0f}")
            else:
                st.warning("No module data available with current filters")

            # Additional tabs for detailed analysis
            st.divider()
            tab1, tab2, tab3, tab4 = st.tabs(
                ["Demographics", "Trend Analysis", "Export", "Database"])

            with tab1:
                st.header("Demographics Analysis")

                # Show demographic distribution
                demographic_cols = processor.get_demographic_columns()
                if demographic_cols:
                    # Calculate demographic totals
                    demo_totals = {}
                    for col in demographic_cols:
                        if col in filtered_data.columns:
                            demo_totals[col] = filtered_data[col].sum()

                    # Create DataFrame for display
                    demo_df = pd.DataFrame(list(demo_totals.items()),
                                           columns=['Demographic', 'Total'])
                    demo_df['Percentage'] = (demo_df['Total'] /
                                             demo_df['Total'].sum() *
                                             100).round(2)
                    demo_df = demo_df.sort_values('Total', ascending=False)

                    # Display table
                    st.dataframe(demo_df, use_container_width=True)

                    # Create pie chart
                    import plotly.express as px
                    fig = px.pie(demo_df,
                                 values='Total',
                                 names='Demographic',
                                 title="Demographic Distribution")
                    st.plotly_chart(fig,
                                    use_container_width=True,
                                    key="demo_analysis_pie")

                # Show raw filtered data
                st.subheader("Filtered Data")
                st.dataframe(filtered_data, use_container_width=True)

            with tab2:
                st.header("Advanced Demographic Trend Analysis")

                demographic_cols = processor.get_demographic_columns()
                if demographic_cols and len(filtered_data) > 0:
                    # Calculate trend data
                    trend_data = processor.calculate_demographic_trends(
                        filtered_data)

                    if not trend_data.empty:
                        # Trend line chart
                        st.subheader("Demographic Trends Across Modules")
                        from utils.visualizations import create_trend_line_chart
                        trend_fig = create_trend_line_chart(
                            trend_data, demographic_cols)
                        st.plotly_chart(trend_fig,
                                        use_container_width=True,
                                        key="trend_line_chart")

                        # Comparative analysis
                        st.subheader("Comparative Analysis")
                        comparisons = processor.calculate_grade_comparisons(
                            filtered_data)

                        if comparisons:
                            comparison_col1, comparison_col2 = st.columns(2)

                            with comparison_col1:
                                st.write("**By Grade Level**")
                                from utils.visualizations import create_comparative_analysis_chart
                                grade_comp_fig = create_comparative_analysis_chart(
                                    comparisons, demographic_cols, 'grade')
                                st.plotly_chart(grade_comp_fig,
                                                use_container_width=True,
                                                key="grade_comparison_chart")

                            with comparison_col2:
                                st.write("**By Component Type**")
                                component_comp_fig = create_comparative_analysis_chart(
                                    comparisons, demographic_cols, 'component')
                                st.plotly_chart(
                                    component_comp_fig,
                                    use_container_width=True,
                                    key="component_comparison_chart")

                        # Diversity metrics
                        st.subheader("Diversity and Equity Metrics")
                        diversity_metrics = processor.calculate_diversity_metrics(
                            filtered_data)

                        if diversity_metrics:
                            # Display metrics in columns
                            metric_col1, metric_col2, metric_col3 = st.columns(
                                3)

                            with metric_col1:
                                simpson_idx = diversity_metrics.get(
                                    'simpson_diversity_index', 0)
                                st.metric(
                                    "Simpson Diversity Index",
                                    f"{simpson_idx:.3f}",
                                    help=
                                    "Measures probability that two randomly selected individuals are from different demographic groups (0-1, higher = more diverse)"
                                )

                            with metric_col2:
                                shannon_idx = diversity_metrics.get(
                                    'shannon_diversity_index', 0)
                                st.metric(
                                    "Shannon Diversity Index",
                                    f"{shannon_idx:.3f}",
                                    help=
                                    "Measures uncertainty in predicting demographic group of random individual (higher = more diverse)"
                                )

                            with metric_col3:
                                balance = diversity_metrics.get(
                                    'representation_balance', 0)
                                st.metric(
                                    "Representation Balance",
                                    f"{balance:.3f}",
                                    help=
                                    "Measures how evenly demographics are distributed (0-1, higher = more balanced)"
                                )

                            # Radar chart for diversity metrics
                            from utils.visualizations import create_diversity_radar_chart
                            radar_fig = create_diversity_radar_chart(
                                diversity_metrics)
                            st.plotly_chart(radar_fig,
                                            use_container_width=True,
                                            key="diversity_radar_chart")

                        # Statistical insights
                        st.subheader("Statistical Insights")

                        # Calculate statistical significance and patterns
                        insights_col1, insights_col2 = st.columns(2)

                        with insights_col1:
                            st.write("**Grade-Level Patterns**")
                            if 'grade_summary' in comparisons:
                                grade_stats = comparisons['grade_summary']

                                # Find grade with highest/lowest diversity
                                for demo_col in demographic_cols[:
                                                                 3]:  # Show top 3 demographics
                                    pct_col = f'{demo_col}_Percentage'
                                    if pct_col in grade_stats.columns:
                                        max_grade = grade_stats.loc[
                                            grade_stats[pct_col].idxmax(),
                                            'Grade']
                                        min_grade = grade_stats.loc[
                                            grade_stats[pct_col].idxmin(),
                                            'Grade']
                                        max_pct = grade_stats[pct_col].max()
                                        min_pct = grade_stats[pct_col].min()

                                        st.write(
                                            f"**{demo_col}:** Highest in Grade {max_grade} ({max_pct:.1f}%), Lowest in Grade {min_grade} ({min_pct:.1f}%)"
                                        )

                        with insights_col2:
                            st.write("**Component-Level Patterns**")
                            if 'component_summary' in comparisons:
                                comp_stats = comparisons['component_summary']

                                # Find component with highest representation
                                for demo_col in demographic_cols[:
                                                                 3]:  # Show top 3 demographics
                                    pct_col = f'{demo_col}_Percentage'
                                    if pct_col in comp_stats.columns:
                                        max_comp = comp_stats.loc[
                                            comp_stats[pct_col].idxmax(),
                                            'Component']
                                        max_pct = comp_stats[pct_col].max()

                                        st.write(
                                            f"**{demo_col}:** Highest in {max_comp[:20]}... ({max_pct:.1f}%)"
                                        )

                        # Trend summary table
                        st.subheader("Trend Summary Table")

                        # Create summary of key trend metrics
                        summary_data = []
                        for demo_col in demographic_cols:
                            pct_col = f'{demo_col}_Percentage'
                            if pct_col in trend_data.columns:
                                mean_pct = trend_data[pct_col].mean()
                                std_pct = trend_data[pct_col].std()
                                min_pct = trend_data[pct_col].min()
                                max_pct = trend_data[pct_col].max()

                                summary_data.append({
                                    'Demographic':
                                    demo_col,
                                    'Average %':
                                    round(mean_pct, 2),
                                    'Std Dev':
                                    round(std_pct, 2),
                                    'Min %':
                                    round(min_pct, 2),
                                    'Max %':
                                    round(max_pct, 2),
                                    'Range':
                                    round(max_pct - min_pct, 2)
                                })

                        if summary_data:
                            summary_df = pd.DataFrame(summary_data)
                            st.dataframe(summary_df, use_container_width=True)
                    else:
                        st.warning(
                            "No trend data available with current filters")
                else:
                    st.warning(
                        "No demographic data available for trend analysis")

            with tab3:
                st.header("📊 Demographic Breakdown")

                # Show demographic distribution
                demographic_cols = processor.get_demographic_columns()
                if demographic_cols:
                    # Calculate demographic totals
                    demo_totals = {}
                    for col in demographic_cols:
                        if col in filtered_data.columns:
                            demo_totals[col] = filtered_data[col].sum()

                    # Create DataFrame for display
                    demo_df = pd.DataFrame(list(demo_totals.items()),
                                           columns=['Demographic', 'Total'])
                    demo_df['Percentage'] = (demo_df['Total'] /
                                             demo_df['Total'].sum() *
                                             100).round(2)
                    demo_df = demo_df.sort_values('Total', ascending=False)

                    # Display table
                    st.dataframe(demo_df, use_container_width=True)

                    # Create pie chart
                    import plotly.express as px
                    fig = px.pie(demo_df,
                                 values='Total',
                                 names='Demographic',
                                 title="Demographic Distribution")
                    st.plotly_chart(fig,
                                    use_container_width=True,
                                    key="export_demo_pie")

                # Show raw filtered data
                st.subheader("📋 Filtered Data")
                st.dataframe(filtered_data, use_container_width=True)

                st.header("💾 Export Options")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📊 Export Data")

                    # Export filtered data
                    excel_buffer = export_to_excel(filtered_data,
                                                   "Filtered_Data")
                    st.download_button(
                        label="📥 Download Filtered Data",
                        data=excel_buffer,
                        file_name="demographic_analysis_filtered.xlsx",
                        mime=
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary")

                    # Export module totals
                    module_totals = processor.calculate_module_totals(
                        filtered_data)
                    if not module_totals.empty:
                        excel_buffer = export_to_excel(module_totals,
                                                       "Module_Totals")
                        st.download_button(
                            label="📋 Download Module Totals",
                            data=excel_buffer,
                            file_name="module_totals.xlsx",
                            mime=
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    # Export comprehensive report
                    demographic_cols = processor.get_demographic_columns()
                    if demographic_cols:
                        from utils.export_utils import export_comprehensive_analysis

                        filters_applied = {
                            'Grade': selected_grades,
                            'Component Desc': selected_components,
                            'EntityDesc': selected_entities
                        }

                        target_demographics = {
                            col: st.session_state.get(f"target_{col}", 10.0)
                            for col in demographic_cols
                        }

                        comprehensive_buffer = export_comprehensive_analysis(
                            filtered_data, filters_applied, demographic_cols,
                            target_demographics, module_totals)

                        st.download_button(
                            label="📊 Download Complete Analysis Report",
                            data=comprehensive_buffer,
                            file_name="complete_demographic_analysis.xlsx",
                            mime=
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                with col2:
                    st.subheader("📈 Export Visualizations")

                    # Export demographic gaps
                    demographic_cols = processor.get_demographic_columns()
                    if demographic_cols:
                        target_demographics = {
                            col: st.session_state.get(f"target_{col}", 10.0)
                            for col in demographic_cols
                        }

                        gaps_df = processor.calculate_demographic_gaps(
                            filtered_data, target_demographics)
                        if not gaps_df.empty:
                            excel_buffer = export_to_excel(
                                gaps_df, "Demographic_Gaps")
                            st.download_button(
                                label="🎯 Download Gaps Analysis",
                                data=excel_buffer,
                                file_name="demographic_gaps.xlsx",
                                mime=
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                        # Export heatmap data
                        heatmap_data = export_heatmap_data(
                            filtered_data, demographic_cols)
                        if not heatmap_data.empty:
                            excel_buffer = export_to_excel(
                                heatmap_data, "Heatmap_Data")
                            st.download_button(
                                label="🔥 Download Heatmap Data",
                                data=excel_buffer,
                                file_name="heatmap_data.xlsx",
                                mime=
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                    st.subheader("📊 Export Charts")
                    st.info(
                        "💡 Use your browser's right-click menu on any chart to save as PNG"
                    )

                    # Instructions for saving charts
                    with st.expander("How to Save Charts"):
                        st.markdown("""
                        **To save any chart:**
                        1. Right-click on the chart
                        2. Select "Save image as..." or "Download plot as a png"
                        3. Choose your save location
                        
                        **Available charts:**
                        - Demographic Heat Map
                        - Module Totals Bar Chart  
                        - Demographic Distribution Pie Chart
                        """)

            with tab3:
                st.header("🗄️ Database Management")

                if not st.session_state.get('db_available', False):
                    st.warning("Database functionality is not available")
                    st.info(
                        "The database feature requires proper configuration. The tool works in file-only mode."
                    )
                else:
                    # Database statistics
                    try:
                        db_stats = db_manager.get_database_stats()
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Datasets",
                                      db_stats['total_datasets'])
                        with col2:
                            st.metric("Total Records",
                                      f"{db_stats['total_records']:,}")
                        with col3:
                            st.metric("Analysis Sessions",
                                      db_stats['total_analyses'])
                    except Exception as e:
                        st.error(f"Database error: {e}")
                        st.session_state.db_available = False

                st.divider()

                # Current dataset info
                if st.session_state.current_dataset_id:
                    db_manager = st.session_state.get('db_manager')
                    if db_manager:
                        dataset_info = db_manager.get_dataset_by_id(
                            st.session_state.current_dataset_id)
                    else:
                        dataset_info = None
                    if dataset_info:
                        st.subheader("Current Dataset")
                        info_col1, info_col2 = st.columns(2)
                        with info_col1:
                            st.write(f"**Name:** {dataset_info['name']}")
                            st.write(
                                f"**Filename:** {dataset_info['filename']}")
                            st.write(
                                f"**Rows:** {dataset_info['rows_count']:,}")
                        with info_col2:
                            st.write(
                                f"**Columns:** {dataset_info['columns_count']}"
                            )
                            st.write(
                                f"**Upload Date:** {dataset_info['upload_date'].strftime('%Y-%m-%d %H:%M')}"
                            )
                            if dataset_info['description']:
                                st.write(
                                    f"**Description:** {dataset_info['description']}"
                                )

                # Save current analysis session - only if database is available
                if st.session_state.get(
                        'db_available',
                        False) and st.session_state.current_dataset_id:
                    st.divider()
                    st.subheader("Save Analysis Session")

                    session_name = st.text_input("Session name:",
                                                 key="session_name")
                    session_notes = st.text_area("Notes (optional):",
                                                 key="session_notes")

                    if st.button("Save Current Analysis", type="primary"):
                        try:
                            # Get current filters and targets
                            filters_applied = {
                                'Grade':
                                selected_grades
                                if 'selected_grades' in locals() else [],
                                'Component Desc':
                                selected_components
                                if 'selected_components' in locals() else [],
                                'EntityDesc':
                                selected_entities
                                if 'selected_entities' in locals() else []
                            }

                            demographic_targets = {
                                'AAM': 15.0,
                                'AAF': 15.0,
                                'PCM': 20.0,
                                'PCF': 20.0,
                                'LGBTF': 10.0,
                                'OTHER_M': 20.0,
                                'OTHER_F': 20.0
                            }

                            # Calculate current results
                            analysis_results = {
                                'filtered_rows':
                                len(filtered_data),
                                'total_people':
                                int(filtered_data['TOTAL'].sum()),
                                'unique_modules':
                                int(filtered_data['EntityDesc'].nunique())
                            }

                            db_manager = st.session_state.get('db_manager')
                            if not db_manager:
                                raise Exception(
                                    "Database manager not available")

                            session_id = db_manager.save_analysis_session(
                                st.session_state.current_dataset_id,
                                session_name, filters_applied,
                                demographic_targets, analysis_results,
                                session_notes)
                            st.success(
                                f"Analysis session saved with ID: {session_id}"
                            )
                        except Exception as e:
                            st.error(f"Error saving analysis session: {e}")

                # List all datasets - only if database is available
                if st.session_state.get('db_available', False):
                    st.divider()
                    st.subheader("All Datasets")
                    try:
                        db_manager = st.session_state.get('db_manager')
                        if db_manager:
                            datasets = db_manager.get_datasets()
                        else:
                            datasets = []
                    except Exception as e:
                        st.error(f"Error loading datasets: {e}")
                        datasets = []

                    if datasets:
                        for dataset in datasets:
                            with st.expander(
                                    f"{dataset['name']} - {dataset['rows_count']:,} rows"
                            ):
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.write(
                                        f"**Filename:** {dataset['filename']}")
                                    st.write(
                                        f"**Upload Date:** {dataset['upload_date'].strftime('%Y-%m-%d %H:%M')}"
                                    )
                                    st.write(
                                        f"**Rows:** {dataset['rows_count']:,}")
                                    st.write(
                                        f"**Columns:** {dataset['columns_count']}"
                                    )
                                    if dataset['description']:
                                        st.write(
                                            f"**Description:** {dataset['description']}"
                                        )

                                with col2:
                                    if st.button(f"Load",
                                                 key=f"load_{dataset['id']}"):
                                        try:
                                            df = db_manager.load_dataset_data(
                                                dataset['id'])
                                            st.session_state.data_processor = DataProcessor(
                                                df)
                                            st.session_state.data = df
                                            st.session_state.current_dataset_id = dataset[
                                                'id']
                                            st.success("Dataset loaded!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error loading: {e}")

                                    if st.button(f"Delete",
                                                 key=f"delete_{dataset['id']}",
                                                 type="secondary"):
                                        if st.session_state.get(
                                                'confirm_delete'
                                        ) == dataset['id']:
                                            try:
                                                db_manager.delete_dataset(
                                                    dataset['id'])
                                                st.success("Dataset deleted!")
                                                st.rerun()
                                            except Exception as e:
                                                st.error(
                                                    f"Error deleting: {e}")
                                        else:
                                            st.session_state.confirm_delete = dataset[
                                                'id']
                                            st.warning(
                                                "Click again to confirm deletion"
                                            )
                    else:
                        st.info("No datasets found in database")
        else:
            st.warning(
                "⚠️ No data matches the selected filters. Please adjust your selection."
            )
    else:
        st.info(
            "ℹ️ Please select at least one option from each filter to view results."
        )

else:
    # Show comprehensive instructions when no data is loaded
    st.info(
        "📁 Please upload an Excel file or load from database to begin analysis"
    )

    # Add how-to-use guide
    st.subheader("📚 How to Use This Tool")

    with st.expander("🎯 Step-by-Step Guide", expanded=True):
        st.markdown("""
        **1. Upload Your Data**
        - Choose "Upload New File" and select your Excel (.xlsx) file
        - Or select "Load from Database" to use previously saved datasets
        
        **2. Review Your Data**
        - Check the file preview to ensure columns are detected correctly
        - Save to database for future use (optional)
        
        **3. Apply Filters**
        - Filter by Grade, Component Description, and specific modules
        - Use the search box to find specific lessons quickly
        
        **4. Analyze Results**
        - **Heat Map**: Shows demographic representation vs your targets
        - **Module Totals**: See total people count per lesson/module
        - **Demographics**: Overall distribution across all selected data
        
        **5. Export Results**
        - Download filtered data, analysis reports, or individual charts
        - Save analysis sessions to database for later review
        """)

    st.subheader("📋 Required File Format")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Required Columns:**
        - `Grade`: Grade level (e.g., "Gr. 1", "Gr. 4")
        - `EntityDesc`: Module/lesson title (e.g., "Lesson, Rosa Parks")
        - `Component Desc`: Activity type (e.g., "Read and Respond")
        - `TOTAL`: Total number of people in the row
        """)

    with col2:
        st.markdown("""
        **Demographic Columns (examples):**
        - `AAM`: African American Male
        - `AAF`: African American Female
        - `PCM`: Pacific Male / `PCF`: Pacific Female
        - `LGBTF`: LGBTQ+ Female
        - `OTHER_M`: Other Male / `OTHER_F`: Other Female
        """)

    st.subheader("🚀 Key Features")

    feature_col1, feature_col2 = st.columns(2)

    with feature_col1:
        st.markdown("""
        **Analysis Tools:**
        - 📈 **Interactive Heat Maps** with configurable targets
        - 📊 **Gap Analysis** showing over/under representation
        - 📋 **Module Totals** with component breakdown
        - 🎯 **Target Comparison** with color-coded results
        """)

    with feature_col2:
        st.markdown("""
        **Data Management:**
        - 🗄️ **Database Storage** for datasets and analysis sessions
        - 🔧 **Smart Filtering** by grade, component, and module
        - 🔍 **Search Functionality** to find specific content
        - 💾 **Comprehensive Export** options (Excel, charts)
        """)

    st.subheader("💡 Understanding the Results")

    with st.expander("Heat Map Interpretation"):
        st.markdown("""
        **Heat Map Colors:**
        - 🟢 **Green**: Over target representation (good diversity)
        - ⚪ **White**: On target representation (meets goals)
        - 🔴 **Red**: Under target representation (needs improvement)
        
        **Target Settings:**
        - Default targets are set to common diversity goals
        - You can customize targets for each demographic in the Heat Map tab
        - Targets represent percentage of total people in each category
        """)

    with st.expander("Module Totals Explained"):
        st.markdown("""
        **Module Summary Table shows:**
        - Total people represented across all components of a module
        - Component breakdown (Read & Respond, activities, etc.)
        - Average representation per component type
        
        **Use this to:**
        - Identify which lessons have the most/least representation
        - Balance content across different modules
        - Ensure adequate sample sizes for analysis
        """)

# Footer section removed

# Add floating AI assistant
from utils.ai_assistant import create_floating_assistant

create_floating_assistant()
