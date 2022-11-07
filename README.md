Онлайн-майданчик для електронної торгівлі та проведення аукціонів, на якому користувачі зможуть виставляти товари, розміщувати ставки та додавати товари до списку відстеження.

eBay-like e-commerce auction site that will allow users to post auction listings, place bids on listings, comment on those listings, and add listings to a “watchlist.”

All requirements can be viewed here: https://cs50.harvard.edu/web/2020/projects/2/commerce/

Installation

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