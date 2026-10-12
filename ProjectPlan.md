Overview:
The goal of this project is to explore how McDonald's restaurant locations are distributed across Illinois and how their distribution relates to income, population, and access to grocery stores. McDonald's is one of the most recognizable fast-food chains in the United States, with restaurants located in urban, suburban, and rural communities. However, the number of restaurants and their locations may vary depending on the characteristics of each community. For this project, we plan to collect and integrate data from three sources: OpenStreetMap, the U.S. Census Bureau, and the U.S. Department of Agriculture (USDA). These datasets will provide information about McDonald's restaurant locations, county-level demographic characteristics, and food access conditions throughout Illinois. We will use Python and Pandas to collect, clean, organize, and integrate the datasets. We will also use GeoPandas to connect restaurant coordinates to Illinois counties. After combining the datasets, we will examine relationships between McDonald's restaurant density, median household income, and food access indicators. The main focus of this project will be the data curation process rather than advanced statistical analysis. We aim to demonstrate how data from different sources can be evaluated, cleaned, and integrated into a single dataset that can be used to answer meaningful research questions. Our final results will include an integrated dataset, documentation of our workflow, and visualizations comparing different counties in Illinois.

Team Members:
Team Member 1: Elizabeth Abraham— Responsible for collecting McDonald's restaurant location data from OpenStreetMap, documenting the acquisition process, and identifying missing or duplicate restaurant records.
Team Member 2: Anishka Khurana— Responsible for collecting demographic data from the U.S. Census Bureau, selecting relevant variables, and cleaning income and population information.
Team Member 3: Mahitha Pamulapati— Responsible for acquiring USDA food access data, reviewing its documentation, and evaluating data quality and limitations.
All team members will contribute to the project plan, data quality assessment, GitHub repository, and final report. We will use GitHub to track contributions and collaborate throughout the project.

Research and Business Questions:
Our main research question is: How does the distribution of McDonald's restaurants across Illinois counties relate to household income, population, and access to grocery stores?
To answer this question, we will investigate the following:
Do counties with higher median household incomes have more or fewer McDonald's restaurants per capita than counties with lower incomes?
How does the number of McDonald's restaurants vary across counties with different population sizes?
Is there a relationship between McDonald's restaurant density and the percentage of residents with limited access to grocery stores?
Are there noticeable differences in McDonald's restaurant distribution between urban and rural counties in Illinois?
These questions will help us understand how fast-food restaurant locations relate to the demographic and food access characteristics of different communities. Our goal is to identify patterns and relationships rather than establish that one factor directly causes another.

Datasets: We plan to use three datasets from publicly accessible sources. Each dataset provides different information needed to answer our research questions. None of the datasets will come from Kaggle.

Dataset 1: McDonald's Restaurant Locations — OpenStreetMap
Source: OpenStreetMap (OSM)
Dataset link: https://www.openstreetmap.org/
Our first dataset will contain McDonald's restaurant locations throughout Illinois. We plan to obtain this information using OpenStreetMap and the Overpass API, which allows users to retrieve geographic features based on attributes such as restaurant name and brand. The dataset is expected to contain information such as restaurant names, latitude, longitude, and available address information. We will also retain OpenStreetMap feature identifiers to help identify duplicate records. This dataset will allow us to determine where McDonald's restaurants are located and calculate the number of restaurants within each Illinois county. One challenge is that OpenStreetMap is maintained by community contributors, meaning some restaurant locations may be missing, outdated, or incorrectly labeled. We will assess these issues during the data quality stage.

Dataset 2: American Community Survey — U.S. Census Bureau
Source: U.S. Census Bureau
Dataset link: https://www.census.gov/data/developers/data-sets/acs-5year.html
API documentation: https://api.census.gov/data/2024/acs/acs5.html
Our second dataset will come from the 2024 American Community Survey (ACS) five-year estimates. This dataset provides demographic and economic information about communities across the United States.
We will focus on Illinois county-level information, including total population and median household income. These variables will help us compare McDonald's restaurant counts across counties with different population sizes and economic conditions. The Census data includes geographic identifiers such as state and county FIPS codes. We will combine these identifiers into a standardized county code to connect the Census data with our other datasets. Because the ACS contains estimates rather than exact counts for every variable, we will document its limitations, including sampling uncertainty and the time period represented by the estimates. 

Dataset 3: Food Access Research Atlas — USDA
Source: U.S. Department of Agriculture, Economic Research Service
Dataset link: https://ers.usda.gov/data-products/food-access-research-atlas/download-the-data
Our third dataset will come from the USDA Food Access Research Atlas. Specifically, we plan to use the 2019 Large Retailer Access Map data, which provides information about access to supermarkets and other large grocery retailers.This dataset contains census-tract-level information about food access, including measures related to income, geographic distance from grocery retailers, and populations experiencing limited food access. We will use these variables to examine whether counties with different levels of grocery store access also have different concentrations of McDonald's restaurants. Since the USDA data is organized by census tract, we will aggregate relevant population counts to the county level before integrating it with the other datasets. The 2019 data also represents an earlier period than our other sources, so we will consider this difference when interpreting the results.

Dataset Integration: 
The three datasets will be integrated using Illinois county identifiers. First, we will obtain McDonald's restaurant coordinates from OpenStreetMap and use geographic boundary data from the U.S. Census Bureau to assign each restaurant to an Illinois county. We will then calculate the number of restaurants in each county. Next, we will prepare the Census demographic data using standardized five-digit county FIPS codes. The USDA food access data will also be grouped by county using the county portion of its census tract identifiers. Once the datasets have been cleaned and organized, we will merge them using the common county FIPS code. This will create one integrated dataset containing McDonald's restaurant counts, population, income, and food access indicators for each Illinois county. We will also calculate the number of McDonald's restaurants per 100,000 residents to make comparisons between counties with different population sizes more meaningful.
Additional geographic data source: U.S. Census Bureau TIGER/Line Shapefiles: https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html

Timeline:
October 12: Complete the project plan, finalize our research questions, identify the three datasets, and submit the project plan through GitHub. All team members will contribute.

October 13–25: Collect the McDonald's restaurant location data, Census demographic data, and USDA food access data. Organize the datasets and document their sources. Team Members 1, 2, and 3 will be responsible for collecting their assigned datasets.

October 26–November 5: Assess the quality of each dataset by checking for missing values, duplicate records, outdated information, and inconsistencies. All team members will participate in the data quality assessment.

November 6–12: Clean the datasets by addressing missing values, removing duplicates, and standardizing geographic identifiers. Team Members 1, 2, and 3 will clean their assigned datasets.

November 13–19: Integrate the three datasets using county identifiers, evaluate the quality of the combined data, and complete the interim status report by November 19. All team members will contribute.

November 20–27: Analyze the integrated dataset to identify relationships between McDonald's restaurant locations, household income, population, and food access. Create visualizations and develop the automated workflow. Team Members 2 and 4 will lead this stage.

November 28–December 3: Complete the project documentation, including the data dictionary, metadata, and instructions for reproducing the results. Test the workflow to make sure it runs correctly. All team members will contribute.

December 4–7: Review and finalize the project, organize the GitHub repository, create the final project release, and submit the completed project by December 7. All team members will participate.

Planned Technical Workflow:
We plan to organize our project using the data lifecycle concepts discussed in class, beginning with acquisition and continuing through quality assessment, cleaning, integration, and analysis. Our raw datasets will be stored separately from cleaned and integrated files. We will use CSV files for tabular data, JSON for API responses and metadata where appropriate, and geographic files for county boundaries. The workflow will use separate Python scripts for data acquisition, quality assessment, cleaning, integration, and visualization. These scripts will be connected through a run-all script so the complete process can be reproduced without manually running each step. We will use SHA-256 checksums to verify downloaded data integrity. We will also conduct a second quality assessment after integration to check whether the resulting records are accurate, complete, consistent, and appropriate for the intended analysis. Our repository will include a README, a requirements file listing software dependencies, a data dictionary, machine-readable project metadata, and documentation explaining how to reproduce the results. We will use relative file paths and test the workflow from a fresh copy of the repository.

Constraints and Limitations:

One potential challenge is the quality and completeness of the McDonald's location data. OpenStreetMap is maintained by contributors, so some restaurants may have missing coordinates, incomplete addresses, or outdated information. We will need to check for duplicate records and ensure that the locations included in our analysis are actually McDonald's restaurants within Illinois. Another limitation is that the datasets represent different time periods. The USDA Large Retailer Access Map data reflects conditions in 2019, while our Census demographic information will use the 2024 ACS five-year estimates. The OpenStreetMap data will represent locations available at the time of extraction. Because these sources are not from the same year, our analysis will be exploratory, and we will avoid making claims about changes over time or direct causal relationships. We may also encounter challenges when integrating geographic data. The datasets use different levels of geographic detail, so we will need to standardize identifiers and aggregate some information to the county level. County-level comparisons may also hide differences between neighborhoods within the same county. We will review the licensing and usage requirements for all sources before redistributing data. OpenStreetMap data is provided under the Open Database License (ODbL), which requires appropriate attribution and may impose conditions on shared databases. We will document source information and relevant reuse requirements in our repository. The Census and USDA data will also be properly cited.

Gaps and Areas Requiring Additional Input:

Although we have identified the three main datasets, there are several details we will need to confirm during the initial stages of the project. First, we need to determine whether OpenStreetMap provides sufficiently complete coverage of McDonald's restaurants across Illinois. If we identify major gaps, we may need to narrow our geographic scope or adjust our research questions. Second, we need to review the USDA variable definitions to select food access measures that can be meaningfully aggregated and compared at the county level. We will also need to determine how to handle missing or unavailable values. Third, we need to verify that the geographic identifiers are compatible across datasets and that the final integrated dataset contains enough complete records for meaningful comparisons. Finally, we will need to become more familiar with geographic data processing in Python, particularly using GeoPandas to connect restaurant coordinates with county boundaries.We expect that some aspects of our project plan may change as we begin working with the actual datasets. However, our overall goal will remain focused on building a clean, well-documented, and reproducible dataset that connects McDonald's restaurant locations with demographic and food access information across Illinois.

References:

OpenStreetMap Contributors. (2026). OpenStreetMap. https://www.openstreetmap.org/

OpenStreetMap Contributors. (2026). Overpass Turbo. https://overpass-turbo.eu/

U.S. Census Bureau. (2024). American Community Survey 5-Year Data. https://www.census.gov/data/developers/data-sets/acs-5year.html

U.S. Department of Agriculture, Economic Research Service. (2021). 2019 Large Retailer Access Map (Food Access Research Atlas) Data. https://ers.usda.gov/data-products/food-access-research-atlas/download-the-data

U.S. Census Bureau. (2024). TIGER/Line Shapefiles. https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html
