# Reconciler

Reconciliation tool for GSTR 2B and Purchase Register (PR) includes Purchase Invoice and CDN

## Installation
Navigate to your bench folder
```
cd frappe-bench
```
Install Reconciler App For Frappe Version 12 and 13 
```
bench get-app reconciler https://github.com/aerele/reconciler.git --branch=master
bench --site [site-name] install-app reconciler
```
Install Reconciler App For Frappe Version 14
```
bench get-app reconciler https://github.com/aerele/reconciler.git --branch=version-14
bench --site [site-name] install-app reconciler
```
## Features
  **Initial implementation is done only for B2B Transactions.
  ### JSON Upload Tool
  
  1. Select appropriate fields and upload GSTR-2B JSON file which is downloaded from [GST portal](https://www.gst.gov.in/).
  2. After creation, for individual transactions in json - 2B entries are automatically generated with the best match of PR.
  3. At the end, you will get overall uploaded and matching summary.

  ![photo_2021-04-21_21-43-26](https://user-images.githubusercontent.com/36359901/115586950-bd7c0280-a2ea-11eb-8c9c-33b2f986c706.jpg)
  ![photo_2021-04-21_21-43-20](https://user-images.githubusercontent.com/36359901/115586937-b8b74e80-a2ea-11eb-87e5-b9a01551e2bb.jpg)


  ### 2B Entry
  1. This is auto-generated entry, where you can find transaction and linked PR matching informations.
  2. Here you have options like ```Rematch Results```, ```Link Supplier```, ```Create Invoice``` , ```Unlink PR```
  3. Account freezing option also given in settings.
  
  ![2bentry](https://user-images.githubusercontent.com/36359901/115589932-0bded080-a2ee-11eb-82a2-0dfed3c919f7.gif)

  ### Matching Tool
  
  1. In this report, you can reconcile the 2B entries with the linked PR's by moving the status from ```pending``` to ```accepted``` state or viceversa based on match status (Both Bulk and individual update actions are applicable).
  2. ```Link/unlink PR``` with the corresponding 2B entry.
  3. ```Create new invoice``` if no PR matched with 2B Entry.
  4. Click on ```view``` option to see differentiate view of the linked entries.
  5. You can only filter entries based on document date range or by return period.
  6. View Type:
      ```Supplier view``` - Supplier wise (tax difference, total pending document, total 2B and PR entry) will be shown.
      ```Document view``` - (** By default it will show all supplier documents. You can also view documents by applying supplier or gstin filters,         otherwise just click on supplier or gstin in ```supplier view``` rows to auto apply filters)
   4. Rows with Match status ```Exact Match``` will be highlighted with blue, ```Accepted``` state in green.
      
  ![report_filters](https://user-images.githubusercontent.com/36359901/115587545-6cb8d980-a2eb-11eb-9d6c-15bcbd3715cb.gif)
  ![photo_2021-04-21_21-40-39](https://user-images.githubusercontent.com/36359901/115586576-5c542f00-a2ea-11eb-99d3-025aaf2ea449.jpg)
  ![document_view](https://user-images.githubusercontent.com/36359901/115589979-1731fc00-a2ee-11eb-863f-5df9ad86e287.gif)

  ### Summary Report
  Here you can find tax account head wise summary
  ![photo_2021-04-21_21-43-49](https://user-images.githubusercontent.com/36359901/115586963-c076f300-a2ea-11eb-9e42-fa04ed008bd1.jpg)

## Dependencies

1. [Frappe](https://github.com/frappe/frappe)
2. [ERPNext](https://github.com/frappe/erpnext)
3. [India Compliance ( Version-14 )](https://github.com/resilient-tech/india-compliance)

## TODO
1. [Next Iteration Fixes](https://github.com/aerele/reconciler/issues/5)
2. [Known Issues](https://github.com/aerele/reconciler/issues/11)

### Show some ❤️ by starring :star: :arrow_up: our repo!
