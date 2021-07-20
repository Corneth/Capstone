#############Imports###############

from kivy.lang import Builder
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.dialog import MDDialog
from kivy.core.window import Window
from kivy.uix.label import Label
import pandas as pd
from kivymd.uix.list import OneLineListItem
import requests
import json
from surprise import Dataset
from surprise import Reader
from surprise.model_selection import train_test_split
from surprise.prediction_algorithms import SVD
from collections import defaultdict

#############Imports###############

Window.size = (600, 500)


#############Functions###############


def get_users():
    users = pd.read_csv('Data/order_database.csv').astype(str)
    users.drop(['Unnamed: 0'], axis=1, inplace=True)
    return users


def get_previous_orders(user_id):
    orders = pd.read_csv('Data/order_database.csv').astype(str)
    orders.drop(['Unnamed: 0'], axis=1, inplace=True)
    previous_orders = orders[orders['user_id'] == user_id]
    return previous_orders


def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=4)
    data = json.loads(text)
    data2 = pd.json_normalize(data['foods'])
    df1 = pd.DataFrame(data2)
    return df1


def nutritional_database(df1):
    df2 = pd.concat([pd.DataFrame(x) for x in df1['foodNutrients']]).reset_index()

    return df2


def fdc_database(para):
    api_key = 'rEEiDOzrf2H2jinxr3JZZqNFLV77B9fZibQPpHG8'
    resp = requests.get('https://api.nal.usda.gov/fdc/v1/foods/search?api_key=' + api_key, params=para)
    if resp.status_code != 200:
        # This means something went wrong.
        print(resp.status_code)

    else:
        try:
            j = resp.json()
            d = jprint(j)
            cols = ['description', 'fdcId', 'foodNutrients', 'ingredients']
            return d[cols]
        except:
            print('Not available')


def search_params(query, pages):
    search_terms = {
        'query': query,
        'pageSize': pages,
        'sortBy': 'dataType.keyword'
    }
    return search_terms


def search_products(user_need):
    result = []
    for item in user_need:
        params = search_params(item, 1)
        result.append(fdc_database(params))

    result1 = pd.concat(result)

    item_code = result1['fdcId'].values[0]
    return item_code


def get_new_samples(df):
    return df.sample(5)


#############Functions###############



#############Empty Classes#################


class Welcome(Screen):
    # empty screen class nothing is needed except the memory space
    pass


class SignIn(Screen):
    # empty screen class nothing is needed except the memory space
    pass


class MainMenu(Screen):
    # empty screen class nothing is needed except the memory space
    pass

#############Empty Classes#################


class P(MDDialog):
    # class for the dialog boxes
    def change_dialog(self, error_text, description_text):
        error = self.ids.title
        description = self.ids.text
        error.text = error_text
        description.text = description_text


class Login(Screen):
    # Login class allows users to login to the application. checks the input of the user id and the password to make
    # sure its correct and allows the user to log in.
    # need to update the login information for when the user logs off. right now the users information stays when you
    # press the logoff button
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def validate_user(self):

        user = self.ids.user
        pwd = self.ids.password
        users = get_users()
        uid = user.text
        passw = pwd.text
        dialog = P()
        if uid == '' or passw == '':
            error = '[color=#FFFFFF]Error[/color]'
            description = '[color=#FF0000]No username or password[/color]'

            dialog.change_dialog(error, description)
            dialog.open()

        elif (users['user_id'].str.contains(uid).any()) & (users['password'].str.contains(passw).any()):
            u = users[users.user_id == uid]
            name = u.at[0, 'name']
            error = '[color=#90ee90]Welcome[/color]'
            description = '[color=#228B22]Welcome ' + name + '  signing in now[/color]'
            dialog.change_dialog(error, description)
            dialog.open()

            sm.current = 'menu'
        else:
            error = '[color=#FFFFFF]Error[/color]'
            description = '[color=#FF0000]Username or password is wrong![/color]'
            dialog.change_dialog(error, description)
            dialog.open()


class SignUp(Screen):
    # Sets the sign up screen to the application. allows users to sign up for an account.
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def check_user(self):
        # Checking to see if the user is in the database (set right now as a csv file for easy access
        name = self.ids.name
        pwd = self.ids.pasw
        uids = self.ids.user_id
        dialog = P()
        username = name.text
        passw = pwd.text
        ide = uids.text
        text_to_list = [ide, username, passw]
        print(text_to_list)
        users = pd.read_csv('Data/sample_users1.csv').astype(str)
        users.drop(['Unnamed: 0'], axis=1, inplace=True)
        if '' in text_to_list:
            # if the user just presses the enter key and doesn't input anything into the fields it will error out and
            # display an error message to inform them what they need to do
            error = '[color=#FFFFFF]Error[/color]'
            description = '[color=#FF0000]No information added please fill out fields[/color]'
            dialog.change_dialog(error, description)
            dialog.open()

        elif users['user_id'].str.contains(ide).any():
            # Checks to see if the user id that they select is actually already in the system. if it is then it
            # errors out and displays a message telling them that they need to choose another one
            error = '[color=#FFFFFF]Error[/color]'
            description = '[color=#FF0000]User ID already taken. Choose another[/color]'
            dialog.change_dialog(error, description)
            dialog.open()

        else:
            error = '[color=#FFFFFF]Welcome[/color]'
            description = '[color=#228B22]Adding new user![/color]'
            dialog.change_dialog(error, description)
            dialog.open()
            user = pd.read_csv('Data/sample_users1.csv').astype(str)
            user.drop(['Unnamed: 0'], axis=1, inplace=True)
            temp_df = pd.DataFrame(columns=['user_id', 'name', 'password'])
            temp_list = pd.Series(text_to_list, index=temp_df.columns)
            temp = temp_df.append(temp_list, ignore_index=True)
            users_new = user.append(temp)
            users_new.to_csv('sample_users1.csv')


class NewOrder(Screen):

    def search(self):
        user_needs = self.ids.search_field.text
        if user_needs == '':
            pop = P()
            error = '[color=#FFFFFF]Error[/color]'
            description = '[color=#FF0000]No information added please fill out field[/color]'
            pop.change_dialog(error,description)
            pop.open()
        else:
            pcode = search_products(user_needs)
            pname = user_needs
            products_container = self.ids.products
            details = BoxLayout(size_hint_y=None, height=20, pos_hint={'top': 1})
            products_container.add_widget(details)
            qty = Label(text='1', size_hint_x=.1, color=(0.6, .45, .45, 1))
            code = Label(text=str(pcode), size_hint_x=.2, color=(0.6, .45, .45, 1))
            name = Label(text=pname, size_hint_x=.3, color=(0.6, .45, .45, 1))

            details.add_widget(qty)
            details.add_widget(code)
            details.add_widget(name)


class PreviousOrder(Screen):
    def on_enter(self, *args):
        self.get_order_details()

    def get_order_details(self):
        app = MDApp.get_running_app()
        prev = get_previous_orders(app.root.get_screen('Login').ids.user.text)
        prev_list = prev['order_id']

        for i in list(set(prev_list)):
            self.ids.prev_container.add_widget(OneLineListItem(text=str(i), on_release=lambda x, value_for_pass=i:
            self.pull_orders(value_for_pass)))

    # uses the frame from newOrder to get all the same stuff as that but will be used for
    # getting the previous orders and getting health information from the original test dataframe
    def pull_orders(self, data):
        prev_order_number = data
        order_list = pd.read_csv('Data/order_database.csv')
        order_list.drop('Unnamed: 0', axis=1, inplace=True)
        item_ids = order_list[order_list['order_id'] == int(prev_order_number)]
        iterate_list = item_ids['product_name'].tolist()
        result = []
        for item in iterate_list:
            params = search_params(item, 1)
            result.append(fdc_database(params))
            self.ids.order_preview.add_widget(OneLineListItem(text=str(item)))
        result1 = pd.concat(result)
        result1.to_csv('checkup.csv')
    list = pd.DataFrame()
    list.to_csv('Data/unformatted_shoppinglist.csv')

    def search_products(self, user_need):

        lists = pd.read_csv('Data/unformatted_shoppinglist.csv')
        params = search_params(user_need, 1)
        items = fdc_database(params)
        shopping_list = lists.append(items)

        shopping_list.to_csv('Data/unformatted_shoppinglist.csv', index=False)
        use_cols = ['description', 'fdcid', 'foodNutrients', 'ingrediants']
        formatted_list = pd.read_csv('Data/unformatted_shoppinglist.csv', usecols=lambda x: x in use_cols, index_col=0)
        formatted_list.to_csv('Data/formatted_list.csv')
#working on getting the previous details to show on the screen through a different layout then a popup widget


class Recommendation(Screen):
    products = pd.read_csv('Data/products.csv')
    aisles = pd.read_csv('Data/aisles.csv')
    departments = pd.read_csv('Data/departments.csv')
    df = pd.merge(products, aisles, on='aisle_id', how='left')
    products_desc = pd.merge(df, departments, on='department_id', how='left')
    departments_to_remove = ['pets','personal care', 'household', 'babies','missing']
    products_food = products_desc[~products_desc['department'].isin(departments_to_remove)]
    ################new#####################
    rec_df = pd.read_csv('rec_df.csv').sample(30000,random_state = 1223)
    rec_df.drop(['Unnamed: 0'],axis = 1, inplace = True)
    rec_df['rating'] = rec_df['count'].apply(lambda x: 5 if (x > 5) else x)
    new_rec_df = rec_df.drop('count',axis = 1)

    reader = Reader(rating_scale=(1, 5))
    new_rec_data = Dataset.load_from_df(new_rec_df, reader)

    short_head = list(new_rec_df.product_id.value_counts()[:6207].cumsum().index)

    ################new#####################

    samples = products_food.sample(5)

    def on_enter(self, *args):
        self.get_sample(self.samples)

    def get_sample(self,samples):

        self.ids.lab_1.text = str(samples['product_name'].iloc[0])
        self.ids.lab_2.text = str(samples['product_name'].iloc[1])
        self.ids.lab_3.text = str(samples['product_name'].iloc[2])
        self.ids.lab_4.text = str(samples['product_name'].iloc[3])
        self.ids.lab_5.text = str(samples['product_name'].iloc[4])

    def ratings(self):
        ratings = [int(self.ids.rating_1.text), int(self.ids.rating_2.text), int(self.ids.rating_3.text),
                   int(self.ids.rating_4.text), int(self.ids.rating_5.text)]

        return ratings

    def get_ratings(self):
        rate = self.ratings()
        ratings_list = []
        samples = self.samples
        app = MDApp.get_running_app()
        userID = app.root.get_screen('Login').ids.user.text

        for i in range(0,5):
            ratings = rate[i]
            rating_one_product = {'user_id': userID, 'product_id': samples['product_id'].iloc[i],'rating': int(
                ratings)}
            ratings_list.append(rating_one_product)

        return ratings_list,userID

    def recommend_diverse_products(self,ranked_products, n, aisle=None, percent_diverse=.20):
        short_head = self.short_head
        num_diverse = round(n * percent_diverse)
        recs = []

        if n < 1:
            print('Number of recommended products must be 1 or more')
            return recs

        for idx, rec in enumerate(ranked_products):

            if n == 0:
                return recs

            prod_id, rating, prod_name, aisle_name = [*rec]

            if aisle:  # Did we specify an aisle?
                if aisle in aisle_name:  # Is it in the aisle we want?
                    if n > num_diverse:  # Are we looking for a long tail product? No
                        name = prod_name
                        self.ids.Recommendations.add_widget(OneLineListItem(text=str('Rec: ' + str(name))))
                        print('Recommendation # ', idx + 1, ': ', name, '\n')
                        recs.append(rec)
                        n -= 1
                    else:  # Are we looking for a long tail product? Yes
                        if prod_id not in short_head:  # Is it NOT in the short_head list?
                            name = prod_name
                            self.ids.Recommendations.add_widget(
                                OneLineListItem(text=str('Rec: ' + str(name))))
                            print('Recommendation # ', idx + 1, ': ', name, '\n')
                            recs.append(rec)
                            n -= 1
                        else:
                            continue
                elif idx == len(ranked_products) - 1:
                    print('No recommended products found')
                    continue
            else:
                if n > num_diverse:  # Are we looking for a long tail product? No
                    name = prod_name
                    self.ids.Recommendations.add_widget(OneLineListItem(text=str('Rec: ' + str(name))))
                    recs.append(rec)
                    n -= 1
                else:  # Are we looking for a long tail product? Yes
                    if prod_id not in short_head:  # Is it NOT in the short_head list?
                        name = prod_name
                        self.ids.Recommendations.add_widget(OneLineListItem(text=str('Rec: ' + str(name))))
                        print('Recommendation # ', idx + 1, ': ', name, '\n')
                        recs.append(rec)
                        n -= 1
                    else:
                        continue
    ################new#####################

    def get_recommendations(self):
        user_rating,userID = self.get_ratings()
        products_desc = self.products_desc
        reader = self.reader
        new_rec_df = self.new_rec_df
        # Adding new ratings to the original ratings DataFrame
        new_ratings_df = new_rec_df.append(user_rating, ignore_index=True)
        new_data = Dataset.load_from_df(new_ratings_df, reader)
        # Training the new model after the data has been added
        new_user_svd = SVD(n_factors=20, n_epochs=10, lr_all=0.005, reg_all=0.4)
        new_user_svd.fit(new_data.build_full_trainset())
        #making predictions for the user
        list_of_products = []

        for product in new_ratings_df['product_id'].unique():
            product_name = products_desc[products_desc['product_id'] == product]['product_name'].iloc[0]
            product_aisle = products_desc[products_desc['product_id'] == product]['aisle'].iloc[0]
            list_of_products.append((product, new_user_svd.predict(userID, product)[3], product_name, product_aisle))

        # Order predictions from highest to lowest
        ranked_products = sorted(list_of_products, key=lambda x: x[1], reverse=True)
        self.recommend_diverse_products(ranked_products,10,aisle = None,percent_diverse = 1)

    ################new#####################

    # Working on getting the final bits of the recommendation system installed into the application
    # Got the ratings information all squared away and now I just need to get the recommended products,recommeded
    # diverse products and finally the new user recommendataion part to operate correctly part to work now. after
    # that i will need to spruce up the actual layout of the application and then it is ready to present.


sm = ScreenManager()


class MainApp(MDApp):

    def toggle_nav_drawer(self):
        popups = P()
        error = '[color=#FFFFFF]Error[/color]'
        description = '[color=#FF0000]In progress. Will be available in next update[/color]'
        popups.change_dialog(error, description)
        popups.open()

    def callback(self):
        popups = P()
        error = '[color=#FFFFFF]Error[/color]'
        description = '[color=#FF0000]In progress. Will be available in next update[/color]'
        popups.change_dialog(error, description)
        popups.open()

    def build(self):
        Builder.load_file('Kivy_files/main.kv')
        Builder.load_file('Kivy_files/signup.kv')
        Builder.load_file('Kivy_files/popup.kv')
        Builder.load_file('Kivy_files/menu.kv')
        Builder.load_file('Kivy_files/neworder.kv')
        Builder.load_file('kivy_files/previousorders.kv')
        Builder.load_file('Kivy_files/recommendation.kv')
        sm.add_widget(Welcome(name='welcome'))
        sm.add_widget(Login(name='Login'))
        sm.add_widget(SignUp(name='SignUp'))
        sm.add_widget(MainMenu(name='menu'))
        sm.add_widget(NewOrder(name='neworder'))
        sm.add_widget(PreviousOrder(name='previousorders'))
        sm.add_widget(Recommendation(name = 'Recommendation'))
        self.theme_cls.accent_hue = '500'
        self.theme_cls.theme_style = 'Dark'
        self.theme_cls.primary_palette = 'Green'
        self.theme_cls.accent_palette = 'LightGreen'
        return sm

if __name__ == '__main__':
    main = MainApp()
    main.run()