"""
OpenCart database models (read-only access)
These models map to the existing OpenCart database tables
"""
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, SmallInteger
from sqlalchemy.ext.declarative import declarative_base

OCBase = declarative_base()


class OCCategory(OCBase):
    """OpenCart category table"""
    __tablename__ = "oc_category"

    category_id = Column(Integer, primary_key=True)
    image = Column(String(255), nullable=True)
    parent_id = Column(Integer, default=0)
    top = Column(Boolean, default=False)
    column = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    status = Column(Boolean, default=True)
    date_added = Column(DateTime, nullable=True)
    date_modified = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<OCCategory {self.category_id}>"


class OCCategoryDescription(OCBase):
    """OpenCart category descriptions (multi-language)"""
    __tablename__ = "oc_category_description"

    category_id = Column(Integer, primary_key=True)
    language_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(255), nullable=True)
    meta_keyword = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<OCCategoryDescription cat={self.category_id} lang={self.language_id}>"


class OCCategoryToStore(OCBase):
    """OpenCart category to store mapping"""
    __tablename__ = "oc_category_to_store"

    category_id = Column(Integer, primary_key=True)
    store_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"<OCCategoryToStore cat={self.category_id} store={self.store_id}>"


class OCProduct(OCBase):
    """OpenCart product table"""
    __tablename__ = "oc_product"

    product_id = Column(Integer, primary_key=True)
    model = Column(String(64), nullable=False)
    sku = Column(String(64), nullable=True)
    upc = Column(String(12), nullable=True)
    ean = Column(String(14), nullable=True)
    jan = Column(String(13), nullable=True)
    isbn = Column(String(17), nullable=True)
    mpn = Column(String(64), nullable=True)
    location = Column(String(128), nullable=True)
    quantity = Column(Integer, default=0)
    stock_status_id = Column(Integer, nullable=True)
    image = Column(String(255), nullable=True)
    manufacturer_id = Column(Integer, nullable=True)
    shipping = Column(Boolean, default=True)
    price = Column(Numeric(15, 4), nullable=False)
    points = Column(Integer, default=0)
    tax_class_id = Column(Integer, nullable=True)
    date_available = Column(DateTime, nullable=True)
    weight = Column(Numeric(15, 8), default=0)
    weight_class_id = Column(Integer, default=0)
    length = Column(Numeric(15, 8), default=0)
    width = Column(Numeric(15, 8), default=0)
    height = Column(Numeric(15, 8), default=0)
    length_class_id = Column(Integer, default=0)
    subtract = Column(Boolean, default=True)
    minimum = Column(Integer, default=1)
    sort_order = Column(Integer, default=0)
    status = Column(Boolean, default=False)
    viewed = Column(Integer, default=0)
    date_added = Column(DateTime, nullable=True)
    date_modified = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<OCProduct {self.product_id} ({self.model})>"


class OCProductDescription(OCBase):
    """OpenCart product descriptions (multi-language)"""
    __tablename__ = "oc_product_description"

    product_id = Column(Integer, primary_key=True)
    language_id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tag = Column(Text, nullable=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(255), nullable=True)
    meta_keyword = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<OCProductDescription prod={self.product_id} lang={self.language_id}>"


class OCProductToCategory(OCBase):
    """OpenCart product to category mapping"""
    __tablename__ = "oc_product_to_category"

    product_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"<OCProductToCategory prod={self.product_id} cat={self.category_id}>"


class OCProductToStore(OCBase):
    """OpenCart product to store mapping"""
    __tablename__ = "oc_product_to_store"

    product_id = Column(Integer, primary_key=True)
    store_id = Column(Integer, primary_key=True)

    def __repr__(self):
        return f"<OCProductToStore prod={self.product_id} store={self.store_id}>"


class OCCustomer(OCBase):
    """OpenCart customer table"""
    __tablename__ = "oc_customer"

    customer_id = Column(Integer, primary_key=True)
    customer_group_id = Column(Integer, nullable=False)
    store_id = Column(Integer, default=0)
    language_id = Column(Integer, nullable=False)
    firstname = Column(String(32), nullable=False)
    lastname = Column(String(32), nullable=False)
    email = Column(String(96), nullable=False)
    telephone = Column(String(32), nullable=False)
    fax = Column(String(32), nullable=True)
    password = Column(String(255), nullable=False)
    salt = Column(String(9), nullable=True)
    cart = Column(Text, nullable=True)
    wishlist = Column(Text, nullable=True)
    newsletter = Column(Boolean, default=False)
    address_id = Column(Integer, default=0)
    custom_field = Column(Text, nullable=True)
    ip = Column(String(40), nullable=True)
    status = Column(Boolean, default=True)
    safe = Column(Boolean, default=False)
    token = Column(Text, nullable=True)
    code = Column(String(40), nullable=True)
    date_added = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<OCCustomer {self.customer_id} ({self.email})>"


class OCOrder(OCBase):
    """OpenCart order table"""
    __tablename__ = "oc_order"

    order_id = Column(Integer, primary_key=True)
    invoice_no = Column(Integer, default=0)
    invoice_prefix = Column(String(26), nullable=True)
    store_id = Column(Integer, default=0)
    store_name = Column(String(64), nullable=True)
    store_url = Column(String(255), nullable=True)
    customer_id = Column(Integer, default=0)
    customer_group_id = Column(Integer, default=0)
    firstname = Column(String(32), nullable=False)
    lastname = Column(String(32), nullable=False)
    email = Column(String(96), nullable=False)
    telephone = Column(String(32), nullable=False)
    fax = Column(String(32), nullable=True)
    custom_field = Column(Text, nullable=True)
    payment_firstname = Column(String(32), nullable=True)
    payment_lastname = Column(String(32), nullable=True)
    payment_company = Column(String(60), nullable=True)
    payment_address_1 = Column(String(128), nullable=True)
    payment_address_2 = Column(String(128), nullable=True)
    payment_city = Column(String(128), nullable=True)
    payment_postcode = Column(String(10), nullable=True)
    payment_country = Column(String(128), nullable=True)
    payment_country_id = Column(Integer, nullable=True)
    payment_zone = Column(String(128), nullable=True)
    payment_zone_id = Column(Integer, nullable=True)
    payment_address_format = Column(Text, nullable=True)
    payment_custom_field = Column(Text, nullable=True)
    payment_method = Column(String(128), nullable=True)
    payment_code = Column(String(128), nullable=True)
    shipping_firstname = Column(String(32), nullable=True)
    shipping_lastname = Column(String(32), nullable=True)
    shipping_company = Column(String(40), nullable=True)
    shipping_address_1 = Column(String(128), nullable=True)
    shipping_address_2 = Column(String(128), nullable=True)
    shipping_city = Column(String(128), nullable=True)
    shipping_postcode = Column(String(10), nullable=True)
    shipping_country = Column(String(128), nullable=True)
    shipping_country_id = Column(Integer, nullable=True)
    shipping_zone = Column(String(128), nullable=True)
    shipping_zone_id = Column(Integer, nullable=True)
    shipping_address_format = Column(Text, nullable=True)
    shipping_custom_field = Column(Text, nullable=True)
    shipping_method = Column(String(128), nullable=True)
    shipping_code = Column(String(128), nullable=True)
    comment = Column(Text, nullable=True)
    total = Column(Numeric(15, 4), default=0)
    order_status_id = Column(Integer, default=0)
    affiliate_id = Column(Integer, nullable=True)
    commission = Column(Numeric(15, 4), nullable=True)
    marketing_id = Column(Integer, nullable=True)
    tracking = Column(String(64), nullable=True)
    language_id = Column(Integer, nullable=False)
    currency_id = Column(Integer, nullable=False)
    currency_code = Column(String(3), nullable=False)
    currency_value = Column(Numeric(15, 8), default=1)
    ip = Column(String(40), nullable=True)
    forwarded_ip = Column(String(40), nullable=True)
    user_agent = Column(String(255), nullable=True)
    accept_language = Column(String(255), nullable=True)
    date_added = Column(DateTime, nullable=False)
    date_modified = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<OCOrder {self.order_id}>"


class OCOrderProduct(OCBase):
    """OpenCart order products"""
    __tablename__ = "oc_order_product"

    order_product_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    model = Column(String(64), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Numeric(15, 4), default=0)
    total = Column(Numeric(15, 4), default=0)
    tax = Column(Numeric(15, 4), default=0)
    reward = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<OCOrderProduct order={self.order_id} product={self.product_id}>"
