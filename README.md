eBay-like e-commerce auction site that will allow users to post auction listings, place bids on listings, comment on those listings, and add listings to a “watchlist.”

All requirements can be viewed here: https://cs50.harvard.edu/web/2020/projects/2/commerce/

Run in Docker:

1. Pull image
 ```
 docker pull theaceofspadeskd/commerce:v1 
 ```
2. Run container  
 ```
 docker run -p 8000:8000 theaceofspadeskd/commerce:v1
 ```   
 

Installation:

1. Download this project
    ```
    git clone https://github.com/theaceofspadeskd/commerce.git
    ```
2. Install all necessary dependencies
    ```
    pip install -r requirements.txt
    ```
3. Make migrations
    ```
    python manage.py makemigrations
    ```
4. Migrate
    ```
    python manage.py migrate
    ```
