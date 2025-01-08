import time
import requests as re
from time import sleep
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from Fakespot.configs import configs
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service


class AmazonReviewScraper:
    def __init__(
        self, username, password):

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--password-store=basic")

        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "autofill.profile_enabled": False,
            "credentials_offer_save_update_password": False,
            "password_manager_offer_save_update_password": False,
            "password_manager_enable_autosignin": False,
            "goog:localPasskeySetting": False  
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("--incognito")

        # Use automatic driver management
        service = Service(ChromeDriverManager().install())

        # Print to verify options (optional, for debugging)
        print(chrome_options.to_capabilities())

        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.logger.info("driver created.")

        self.username = username
        self.password = password
        self.transaction_id_list = []
        self.signed_in = False
        self.sign_in_url = configs["urls"]["sign_in_url"]
        self.review_page_url = configs["urls"]["review_page_url"]
        self.list_product_url = configs["urls"]["list_product_url"]

    def sign_in(self):
        """Sign in amazon to get product list and review etc."""

        self.driver.get(self.sign_in_url)

        try:
            elem = self.driver.find_element(By.NAME, "email")
            elem.send_keys(self.username)
            self.driver.find_element(By.ID, "continue").click()

            elem = self.driver.find_element(By.NAME, "password")
            elem.send_keys(self.password)
            self.driver.find_element(By.ID, "signInSubmit").click()
        except Exception as exc:
            self.logger.info(
                f"Exception attempting to sign in {exc}. Checking if worker already signed in."
            )

        self.signed_in = True
        self.logger.info(f"Worker signed in!")
        return True

    def terminate(self):
        """Terminate the driver."""

        self.driver.quit()

    def _scroll_down(self):
        """A method for scrolling the page."""

        time.sleep(self.times_dict["wait_time"])

        # Get scroll height.
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        n_page = 0
        while True:

            # Scroll down to the bottom.
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )

            # Wait to load the page.
            time.sleep(self.times_dict["long_wait_time"])

            # Calculate new scroll height and compare with last scroll height.
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:

                break

            last_height = new_height
            self.logger.debug(f"Scrolling... Page {n_page}")
            n_page += 1
        from time import sleep

    def find_similar_product_review_rating_counts(self, total_page):
        """Get the text on the total ratings and review from the product review pages for the given list of product.
        Args:
            total_page: int, number of total pages to get the count for the product on those pages.
        Return:
            product_review_count: (dict) dictionray with product url as key and the string of the review and rating counts as value."""

        product_review_count = {}
        current_page = self.list_product_url

        # the the page of product list
        self.driver.get(current_page)

        # get all items from the product list page and loop over it
        e = self.driver.find_elements(By.CSS_SELECTOR, "[role^='listitem']")
        for idx in range(len(e)):
            try:
                self._get_rating_review_text(product_review_count, current_page, idx)
            except Exception as e:
                print(f"page 1, index {idx} read failed.")
        
        # move on to the next page until total page is reached
        for page_n in range(2, total_page):

            print(f"a[href*='page={page_n}']")
            self.driver.find_element(By.CSS_SELECTOR, f"a[href*='page={page_n}']").click()
            current_page = self.driver.current_url
            sleep(5)

            e = self.driver.find_elements(By.CSS_SELECTOR, "[role^='listitem']")
            for idx in range(len(e)):
                try:
                    self._get_rating_review_text(product_review_count, current_page, idx)
                except Exception as e:
                    print(f"index {idx} read failed.")
        return product_review_count

    def _get_rating_review_text(self, product_review_count, current_page, idx):
        """
        Helper method to click through the pages to find the page with the target text and extract the string.
        Args:
            product_review_count: dictionary that stores review and rating count string
            current_page: the url of the current page
            idx: the index of the item on this page
        """

        self.driver.get(current_page)
        sleep(3)
        ee = self.driver.find_elements(By.CSS_SELECTOR, "[role^='listitem']")
        i = ee[idx]
        ele = i.find_element(By.CSS_SELECTOR, "a[class='a-link-normal s-line-clamp-2 s-link-style a-text-normal']")
        ele.click()
        product_url = self.driver.current_url
        self.driver.find_element(By.ID, "acrCustomerReviewText").click()
        self.driver.find_element(By.CSS_SELECTOR, "a[data-hook='see-all-reviews-link-foot']").click()
        t = self.driver.find_element(By.CSS_SELECTOR, "div[data-hook='cr-filter-info-review-rating-count']").text
        product_review_count[product_url] = t

    def find_all_reviews(self, review_page=None, n_page_to_get_review=None):
        """
        Get all reviews and its key properties on the reviews.
        Args:
            review_page: URL of the page to get all the reviews.
            n_page_to_get_review: integer on how many pages that to extract the reviews.
        Return:
            review_dict: dictionary on the review of the product.
        """
        
        review_dict = {}
        if review_page:
            self.driver.get(review_page)
        else:
            self.driver.get(self.review_page_url)
        self.driver.find_element(By.CLASS_NAME, "a-dropdown-prompt").click()
        sleep(1)
        self.driver.find_element(By.XPATH, "//a[text()='Most recent']").click()
        sleep(1)
        self._set_reviews_for_product(review_dict)

        n_page_to_get_review = 10 if n_page_to_get_review is None else n_page_to_get_review
        for i in range(2, n_page_to_get_review):
            sleep(5)
            print(f"a[href*='pageNumber={i}']")
            try:
                self.driver.find_element(By.CSS_SELECTOR, f"a[href*='pageNumber={i}']").click()
                sleep(2)
                self._set_reviews_for_product(review_dict)
            except:
                break
        return review_dict

    def _set_reviews_for_product(self, review_dict):
        """
        Helper method to set the review details to the dict for all reviews on this page.
        Args:
            review_dict: dictionay that stores review id and dictionary on the review's properties.
        """

        review_ids = self.driver.find_elements(By.CSS_SELECTOR, "[id^='customer_review-']")
        for review_element in review_ids:
            review_id = review_element.get_attribute("id").replace("customer_review-","")
            review_dict.setdefault(review_id, {})
            review_dict[review_id]["has_image"] = self.has_review_images(review_element)
            review_dict[review_id]["has_video"] = self.has_review_video(review_element)
            review_dict[review_id]["review_text"] = self.get_review_text(review_element)
            review_dict[review_id]["review_date"] = self.get_review_date(review_element)
            review_dict[review_id]["review_rating"] = self.get_review_rating(review_element)
    
    def get_fakespot_grade(self, product_url):
        """
        Get the fakespot grade for a given product with its url.
        Args:
            product_url: URL of the targeted product.

        Returns:
            String of the rate from fakespot, e.g. "A", "F".
        """

        fakespot_url = "https://www.fakespot.com/analyzer"
        self.driver.get(fakespot_url)
        e = self.driver.find_element(By.ID, "url-input-home")
        e.send_keys(product_url)
        self.driver.find_element(By.XPATH,"//button[@name='button' and @type='submit' and @class='submit-button fs-bg-blue']/span[@class='dm2' and text()='Analyze']").click()
        fakespot_rate = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'review-grade') and contains(@class, 'interFont') and contains(@class, 'grade-box')]").text

        return fakespot_rate

    @staticmethod
    def has_review_images(review_element):
        """
        Checks if a given review element contains images.
        Args:
            review_element: A Selenium WebElement representing the review container.

        Returns:
            True if the review has images, False otherwise.
        """
        try:
            # Find the image container within the review element.
            image_container = review_element.find_element(By.CLASS_NAME, "review-image-container")
            return True  
        except Exception as e:
            # If an exception is raised, it means no image container was found
            return False 
        
    @staticmethod
    def get_review_text(review_element):
        """
        Extracts the review text from a given review element.
        Args:
            review_element: A Selenium WebElement representing the review container.

        Returns:
            The review text as a string, or None if not found.
        """
        try:
            # Find the review text element with the data-hook
            review_text_element = review_element.find_element(By.CSS_SELECTOR, "[data-hook='review-body']")
            return review_text_element.text
        except Exception as e:
            print(f"Error getting review text: {e}")
            return None

    @staticmethod
    def get_review_date(review_element):
        """
        Extracts the review text from a given review element.
        Args:
            review_element: A Selenium WebElement representing the review container.

        Returns:
            The review text as a string, or None if not found.
        """
        try:
            # Find the review text element with the data-hook
            review_date_element = review_element.find_element(By.CSS_SELECTOR, "[data-hook='review-date']")
            return review_date_element.text
        except Exception as e:
            print(f"Error getting review text: {e}")
            return None

    @staticmethod
    def get_review_rating(review_element):
        """
        Extracts the review text from a given review element.
        Args:
            review_element: A Selenium WebElement representing the review container.

        Returns:
            The review text as a string, or None if not found.
        """
        try:
            # Find the review text element with the data-hook
            review_rating_element = review_element.find_element(By.CSS_SELECTOR,  "i[data-hook='review-star-rating']")
            rating = int(review_rating_element.get_attribute("class").split("a-star-")[1].split(" ")[0])
            return rating
        except Exception as e:
            print(f"Error getting review text: {e}")
            return None
    
    @staticmethod
    def has_review_video(review_element):
        """
        Extracts the review text from a given review element.

        Args:
            review_element: A Selenium WebElement representing the review container.

        Returns:
            The review text as a string, or None if not found.
        """
        try:
            # Find the review text element with the data-hook
            video_element = review_element.find_element(By.CLASS_NAME, "vjs-poster")
            return True 
        except Exception as e:
            return False
    
    @staticmethod
    def extract_ratings_and_reviews(text):
        """
        Extracts two integers representing total ratings and ratings with reviews
        from a string.
        Args:
            text: A string containing the numbers, typically in the format
                "10,349 total ratings, 3,290 with reviews".

        Returns:
            A tuple containing two integers: (total_ratings, ratings_with_reviews).
            Returns (None, None) if extraction fails.
        """
        match = re.match(r"(\d{1,3}(?:,\d{3})*)\s+total ratings,\s*(\d{1,3}(?:,\d{3})*)\s+with reviews", text)
        if match:
            total_ratings = int(match.group(1).replace(",", ""))
            ratings_with_reviews = int(match.group(2).replace(",", ""))
            return (total_ratings, ratings_with_reviews)
        else:
            return (None, None)