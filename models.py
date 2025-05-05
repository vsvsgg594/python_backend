import datetime
from database import Base
from sqlalchemy import Column, Integer,String, DateTime,ForeignKey, Text, Float, Time, Date, ARRAY,JSON
from datetime import datetime
from sqlalchemy.orm import relationship




class addressTable(Base):
    __tablename__ = "address"

    addressId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    addressField = Column(String(1000))
    state = Column(String(255))
    city = Column(String(255))
    zipCode = Column(String(100))
    isDefault = Column(Integer)
    status = Column(Integer, default = 0)
    addedAt = Column(DateTime, default=datetime.now)

    addressrelation1 = relationship('users', back_populates="userrelation1")
    # addressrelation2 = relationship('ordersTable', back_populates="orderRelation3")

#userType
# 0 = customer
# 1 = deliveryAgent
# 2 = merchant
# 3 = admin 

class users(Base):
    __tablename__ = "user"

    userId = Column(Integer, primary_key=True, autoincrement=True)
    userName = Column(String(255))
    userEmail = Column(String(255))
    userPhone = Column(String(255))
    userType = Column(Integer, default=0)
    password = Column(String(255), default=None)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)
    referralCode = Column(String(255), nullable=True)
    referredBy = Column(Integer,nullable=True)
    referralPoints = Column(Float, default=0)

    userrelation1 = relationship('addressTable', back_populates="addressrelation1")
    userrelation2 = relationship('userDetailsTable', back_populates="userDetailRelation1")
    userrelation3 = relationship('userLocationTable', back_populates="userLocationRelation1")
    userrelation4 = relationship('userPrivilagesTable', back_populates="userPrivilageRelation1")
    userrelation5 = relationship('deliveryAgentReviewsTable', back_populates="deliveryAgentReviewRelation1", foreign_keys='deliveryAgentReviewsTable.ratedByUser')
    userrelation6 = relationship('deliveryAgentReviewsTable', back_populates="deliveryAgentReviewRelation2", foreign_keys='deliveryAgentReviewsTable.deliveryAgentId')
    userrelation7 = relationship('deliveryReportTable', back_populates="deliveryReportRelation1")
    userrelation8 = relationship('earningsTable', back_populates="earningsTableRelation1")
    userrelation9 = relationship('loyalityPointsTable', back_populates="loyalityPointsRelation1")
    userrelation10 = relationship('merchantTable', back_populates="merchantTableRelation1")
    userrelation11 = relationship('productReviewTable', back_populates="productreviewrelation2")
    userwishlist = relationship('wishlistTable', back_populates="wishlistuser")
    userorder = relationship('ordersTable', back_populates="ordereduser", foreign_keys='ordersTable.userId')
    userdeliveryagent = relationship("orderDeliveryModel", back_populates="deliveryagentuser")
    userdeliveryagentlog = relationship("deliveryAgentLog", back_populates="deliveryagentloguser")
    userdeliveryagentpersonal = relationship("deliveryAgentPersonalData", back_populates="deliveryagentpersonal")
    deliveryAgentorder = relationship("ordersTable", back_populates="orderdeliveryAgent", foreign_keys='ordersTable.deliveryAgentId')
    usersmanagertable=relationship("ManagerTable",back_populates="managertableusers")
    usermerchantreview = relationship('merchantReviewTable', back_populates="merchantreviewuser")
    usergiftcard = relationship("buyGiftCard", back_populates="giftcarduser")
     
class userDetailsTable(Base):
    __tablename__ = "userDetails"

    userDetailsId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    userName=Column(String(255),nullable=True)
    userDOB=Column(Date,nullable=True)
    #userType = Column(Integer, default=0)
    bankAccountNumber = Column(String(255),nullable=True)
    bankAccountHolder = Column(String(255),nullable=True)
    bankIfscCode = Column(String(255),nullable=True)
    bankBranch = Column(String(255),nullable=True)
    upiId = Column(String(255),nullable=True)
    status = Column(Integer, default= 0)
    # merchantId = Column(Integer,ForeignKey('merchants.merchantId'), nullable=True)
    addedAt = Column(DateTime, default=datetime.now)

    userDetailRelation1 = relationship('users', back_populates="userrelation2")


class userLocationTable(Base):
    __tablename__ = "userLocation"

    userLocationId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    #merchantId = Column(Integer, ForeignKey('merchants.merchantId'))
    latitude = Column(String(255))
    longtitude = Column(String(255))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    userLocationRelation1 = relationship('users', back_populates="userrelation3")
    #userLocationRelation2 = relationship('merchantTable', back_populates="merchantTableRelation2")

class userPrivilagesTable(Base):
    __tablename__ = "userPrivilages"

    privilageId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    canHandleOrders = Column(Integer)
    canHandleMerchants = Column(Integer)
    canHandleDeliveryBoy = Column(Integer)
    canHandleProducts = Column(Integer)
    canHandleCustomers = Column(Integer)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    userPrivilageRelation1 = relationship('users', back_populates="userrelation4")

class categoryTable(Base):
    __tablename__ = "category"

    categoryId = Column(Integer, primary_key=True, autoincrement=True)
    categoryName = Column(String(300))
    categoryImage = Column(Integer, ForeignKey('gallery.imageId'))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    categoryrelation1 = relationship('subCategoryTable', back_populates="subcategoryrelation1")
    categoryrelation2 = relationship('productsTable', back_populates = "productstablerelation2")
    categoryimagerelation = relationship('productGallery', back_populates="imagecategory")

class subCategoryTable(Base):
    __tablename__ = "subCategories"

    subCategoryId = Column(Integer, primary_key=True, autoincrement=True)
    categoryId = Column(Integer, ForeignKey('category.categoryId'))
    subcategoryName = Column(String(300))
    subcategoryImage = Column(Integer, ForeignKey('gallery.imageId'))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    subcategoryrelation1 = relationship('categoryTable', back_populates="categoryrelation1")
    subcategoryrelation2 = relationship('productsTable', back_populates = "productstablerelation3")
    subcategoryImagerelation = relationship('productGallery', back_populates= "imagesubcategory")

class couponsTable(Base):
    __tablename__ = "coupons"

    couponId = Column(Integer, primary_key=True, autoincrement=True)
    couponname=Column(String)
    typeOfCoupon = Column(Integer)
    code =Column(String(10))
    description = Column(String)
    price = Column(Float)
    startingdate = Column(DateTime)
    endingdate = Column(DateTime)
    maxValue=Column(Integer)
    maxAllowedUsers=Column(Integer)
    minOrderAmount= Column(Integer, default= 0)
    UsersCount = Column(Integer)
    allowToUseMultipleTimes = Column(Integer, default=0) #0 off 1 on
    allowLoyalityPointsRedeem = Column(Integer, default=0)
    allowLoyalityPointsEarned = Column(Integer, default=0)
    status=Column(Integer, default= 0)
    
    couponsTableRelation1 = relationship('orderCouponsTable', back_populates="ordersCouponRelation2")

class deliveryAgentReviewsTable(Base):
    __tablename__ = "deliveryAgentReviews"

    deliveryAgentReviewId = Column(Integer, primary_key=True, autoincrement=True)
    deliveryAgentId = Column(Integer, ForeignKey('user.userId'))
    rating = Column(String(300))
    comments = Column(Text)
    ratedByUser = Column(Integer, ForeignKey('user.userId'))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    deliveryAgentReviewRelation1 = relationship('users', back_populates="userrelation5",foreign_keys=[ratedByUser])
    deliveryAgentReviewRelation2 = relationship('users', back_populates="userrelation6", foreign_keys=[deliveryAgentId])


class deliveryReportTable(Base):
    __tablename__ = "deliveryReport"

    deliveryReportId = Column(Integer, primary_key=True, autoincrement=True)
    orderId = Column(Integer, ForeignKey('orders.orderId'))
    userId = Column(Integer, ForeignKey('user.userId'))
    customerLatitude = Column(String(300))
    customerLogtitude = Column(String(300))
    deliveryTime = Column(DateTime)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    deliveryReportRelation1 = relationship('users', back_populates="userrelation7")
    deliveryReportRelation2 = relationship('ordersTable', back_populates="orderRelation1")

class earningsTable(Base):
    __tablename__ = "earnings"

    earningsId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    basePay = Column(String(300))
    tip = Column(String(300))
    incentive = Column(String(300))
    totalEarnings = Column(String(300))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    earningsTableRelation1 = relationship('users', back_populates="userrelation8")

class loyalityPointsTable(Base):
    __tablename__ = "loyalityPoints"

    loyalityPointsId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    points = Column(Float, default=0)
    #earnedAt = Column(DateTime)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    loyalityPointsRelation1 = relationship('users', back_populates="userrelation9")

class merchantTable(Base):
    __tablename__ = "merchants"

    merchantId = Column(Integer, primary_key=True, autoincrement=True)
    shopName = Column(String(500))
    handledByUser = Column(Integer, ForeignKey('user.userId'))
    shopEmail = Column(String(255))
    coverImage = Column(Integer, ForeignKey('gallery.imageId'))
    phoneNumber = Column(String(30))
    address = Column(String(1000))
    displayAddress = Column(String(1000))
    #tags = Column(String(1000))
    description = Column(Text)
    merchantPoints = Column(Integer, default= 0)
    rating = Column(Float, default= 0)
    servingRadius = Column(Integer, default= None)
    latitude = Column(String(1000))
    longitude = Column(String(1000))
    openingTime = Column(Time)
    closingTime = Column(Time)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)
    shopStatus = Column(Integer, default=0)


    merchantTableRelation1 = relationship('users', back_populates="userrelation10")
    #merchantTableRelation2 = relationship('userLocationTable', back_populates="userLocationRelation2")
    merchantTableRelation3 = relationship('ordersTable', back_populates="orderRelation2")
    merchanttablerelation4 = relationship('productsTable', back_populates="productstablerelation1")
    merchantImage = relationship('productGallery', back_populates="imageMerchant")
    merchantbanner = relationship('Banner', back_populates="bannermerchant")
    searchmerchant = relationship("searchTable", back_populates='merchantsearch')
    merchantreview = relationship('merchantReviewTable', back_populates="reviewmerchant")
    merchantdiscount = relationship("discountMerchantTable", back_populates="discountmerchants")



class ordersTable(Base):
    __tablename__ = "orders"

    orderId = Column(Integer, primary_key=True, autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    merchantId = Column(Integer, ForeignKey('merchants.merchantId'))
    #addressId = Column(Integer, ForeignKey('address.addressId'))
    orderStatus = Column(Integer, default=0) # 0 pending, 1 dispatched,2 completed
    totalAmount = Column(Float, default=0)
    paymentMethod = Column(String(255)) #0 razor pay 1 cod
    tipAmount = Column(Float,default=0)
    deliveryMode = Column(Integer) # 0 door delivery 1 take away
    deliveryInstruction = Column(Text, default=None)
    merchantInstruction = Column(Text, default=None)
    latitude = Column(String(100))
    longitude = Column(String(100))
    orderOtp = Column(Integer, nullable=True)
    deliveryAgentId = Column(Integer, ForeignKey('user.userId'), nullable=True)
    deliveryCharge = Column(Float, nullable=True)
    orderedAddress = Column(String(1000))
    valueReduced = Column(Float, nullable=True)
    durationFromMerchant = Column(Integer, nullable=True)
    distanceFromMerchant = Column(Float, nullable=True)
    status = Column(Integer, default= 0) # 0 booked 1 cancelled 
    addedAt = Column(DateTime, default=datetime.now)

    


    orderRelation1 = relationship('deliveryReportTable', back_populates="deliveryReportRelation2")
    orderRelation2 = relationship('merchantTable', back_populates="merchantTableRelation3")
    #orderRelation3 = relationship('addressTable', back_populates="addressrelation2")
    orderRelation4 = relationship('orderCouponsTable', back_populates="ordersCouponRelation1")
    orderRelation5 = relationship('orderItemsTable', back_populates="orderItemsRelation1")
    ordereduser = relationship('users', back_populates="userorder", foreign_keys=[userId])
    orderdeliveryrelation = relationship("orderDeliveryModel", back_populates="deliveryorderrelation")
    orderdeliveryAgent = relationship("users", back_populates="deliveryAgentorder", foreign_keys=[deliveryAgentId])
    orderrefund = relationship("refundModel", back_populates="refundorder")
    orderpayment = relationship("payments", back_populates= "paymentorder")
    


class orderCouponsTable(Base):
    __tablename__ = "orderCoupons"

    orderCouponId = Column(Integer, primary_key=True, autoincrement=True)
    orderId = Column(Integer, ForeignKey('orders.orderId'))
    couponId = Column(Integer, ForeignKey('coupons.couponId'))
    valueReduced = Column(Integer)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    ordersCouponRelation1 = relationship('ordersTable', back_populates="orderRelation4")
    ordersCouponRelation2 = relationship('couponsTable', back_populates="couponsTableRelation1")

class orderItemsTable(Base):
    __tablename__ = "orderItems"

    orderItemId = Column(Integer, primary_key=True, autoincrement=True)
    orderId = Column(Integer, ForeignKey('orders.orderId'))
    productId = Column(Integer, ForeignKey('products.productId'))
    quantity = Column(Integer)
    price = Column(Float)
    productTotal = Column(Float)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    orderItemsRelation1 = relationship('ordersTable', back_populates="orderRelation5")
    orderItemsRelation2 = relationship('productsTable', back_populates="productstablerelation4")

class taxTable(Base):
    __tablename__ = "tax"

    taxId = Column(Integer, primary_key=True, autoincrement=True)
    taxName = Column(String(255))
    tax = Column(Float)
    taxType = Column(Integer) # 1 price 2 percentage
    ApplicableOn = Column(String(255))
    differentiate = Column(Integer, default=0) #0 normal 1 merchant
    status = Column(Integer, default= 0) #0 active 1 inactive
    deleteStatus = Column(Integer, default=0) #0 not deleted 1 deleted

    taxproductrelation = relationship('productTaxTable', back_populates="producttaxrelation")

class productTaxTable(Base):
    __tablename__ = "productTax"

    orderTaxId = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey('products.productId'))
    taxId = Column(Integer, ForeignKey('tax.taxId'))
    taxAmount =  Column(Float)

    producttaxrelation = relationship('taxTable', back_populates="taxproductrelation")
    producttaxproducttable = relationship('productsTable', back_populates="productstabletax")

class productsTable(Base):
    __tablename__ = "products"

    productId = Column(Integer, primary_key=True, autoincrement=True)
    productName = Column(String(1000))
    price = Column(Integer)
    costPrice = Column(Integer)
    description = Column(Text)
    longDescription = Column(Text)
    #searchTag = Column(String(200))
    minimumQuantity = Column(Integer)
    maximumQuantity = Column(Integer)
    sku = Column(String(300))
    priorityOrder = Column(Integer, default=1)
    categoryId = Column(Integer, ForeignKey('category.categoryId'))
    subCategoryId = Column(Integer, ForeignKey('subCategories.subCategoryId'))
    isVeg = Column(Integer, default=0)
    preparationTime = Column(String(1000))
    merchantId = Column(Integer, ForeignKey('merchants.merchantId'))
    isAvailable = Column(Integer,default=0)
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)
    discountId=Column(Integer, ForeignKey('discount.discountId'))

    productstablerelation1 = relationship('merchantTable', back_populates="merchanttablerelation4")
    productstablerelation2 = relationship('categoryTable', back_populates = "categoryrelation2")
    productstablerelation3 = relationship('subCategoryTable', back_populates = "subcategoryrelation2")
    productstablerelation4 = relationship('orderItemsTable', back_populates="orderItemsRelation2")
    productstablerelation5 = relationship('productAvailabilityTable', back_populates="productavailability1")
    productstablerelation6 = relationship('productReviewTable', back_populates="productreviewrelation1")
    productstablerelation7 = relationship('productScheduleTable', back_populates="productschedule2")
    productstablerelation8 = relationship('productImages', back_populates="imageRelation1")
    # productstablerelation9 = relationship('discountTable', back_populates="discountrelation1")
    productcartrelation = relationship('cartTable', back_populates="cartproductrelation")
    productwishlist = relationship('wishlistTable', back_populates="wishlistproduct")
    productstabletax = relationship('productTaxTable', back_populates="producttaxproducttable")
    searchproduct = relationship("searchTable", back_populates='productsearch')


class productImages(Base):
    __tablename__ = "productImage"

    productImageId = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey('products.productId'))
    imageId = Column(Integer, ForeignKey('gallery.imageId'))

    imageRelation1 = relationship('productsTable', back_populates="productstablerelation8")
    imageRelation2 = relationship('productGallery', back_populates="galleryrelation1")
    # imagecart = relationship('cartTable', back_populates="cartimagerelation")
    


class productGallery(Base):
    __tablename__ = "gallery"

    imageId = Column(Integer, primary_key=True, autoincrement=True)
    imageName = Column(String(1000))
    imageAlt = Column(String(1000))
    uploadedBy = Column(Integer)

    galleryrelation1 = relationship('productImages', back_populates="imageRelation2")
    imageMerchant = relationship('merchantTable', back_populates="merchantImage")
    gallerybanner = relationship('Banner', back_populates="bannergallery")
    imagecategory = relationship('categoryTable', back_populates="categoryimagerelation")
    productgallerygiftcard=relationship('Giftcard',back_populates="giftcardproductgallery")
    imagesubcategory = relationship('subCategoryTable', back_populates= "subcategoryImagerelation")

class productAvailabilityTable(Base):
    __tablename__ = "productAvailability"

    productAvailabilityId = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey('products.productId'))
    # scheduleId = Column(Integer, ForeignKey('productSchedule.productScheduleId'))
    isAvailable = Column(Integer, default= 0)
    orderAcceptanceTime = Column(String(255))
    # startTime = Column(String(300))
    # endTime = Column(String(300))
    addedAt = Column(DateTime, default=datetime.now)

    productavailability1 = relationship('productsTable', back_populates="productstablerelation5")
    #productavailability2 = relationship('productScheduleTable', back_populates="productschedule1")
    

class productReviewTable(Base):
    __tablename__ = "productReview" 

    productReviewId = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey('products.productId'))
    rating = Column(String(300))
    comment = Column(Text)
    reviewedByUser = Column(Integer, ForeignKey('user.userId'))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    productreviewrelation1 = relationship('productsTable', back_populates="productstablerelation6")
    productreviewrelation2 = relationship('users', back_populates="userrelation11")

class productScheduleTable(Base):
    __tablename__ = "productSchedule"

    productScheduleId = Column(Integer, primary_key=True, autoincrement=True)
    productId = Column(Integer, ForeignKey('products.productId'))
    startTime = Column(String(300))
    endTime = Column(String(300))
    days = Column(String(300))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    #productschedule1 = relationship('productAvailabilityTable', back_populates="productavailability2")
    productschedule2 = relationship('productsTable', back_populates="productstablerelation7")


class otpStore(Base):
    __tablename__ = 'otpTable'

    slno = Column(Integer, primary_key=True, autoincrement=True)
    userEmail = Column(String(1000))
    otp = Column(String(10))
    status = Column(Integer, default= 1)
    timestamp = Column(String(30))


class messageTable(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True,autoincrement=True)
    message = Column(Text)
    senderId = Column(String(30))
    receiverId = Column(String(30))
    storeId = Column(Integer, nullable=True)
    receiverStoreId = Column(Integer, nullable=True)
    jsonMessage = Column(JSON, nullable=True)
    clientconnectionId = Column(String(12), nullable=True)
    receiverconnectionId = Column(String(12), nullable=True)
    timestamp= Column(DateTime, default=datetime.now)


class discountTable(Base):
    __tablename__ = "discount"
    
    discountId = Column(Integer,primary_key=True,autoincrement=True)
    discountType=Column(Integer) #1 percent 0 fixed
    discountName = Column(String(200)) 
    discountValue=Column(Float)
    minimumOrderAmount = Column(Float)
    description=Column(String)
    validfrom=Column(DateTime)
    validto=Column(DateTime)
    maxiamt=Column(Float)
    status = Column(Integer, default=1)

    #discountrelation1 = relationship('productsTable', back_populates="productstablerelation9")
    tablediscount = relationship("discountMerchantTable", back_populates="discounttable") 

class Banner(Base):
    __tablename__="banner"
    bannerid= Column(Integer,primary_key=True,autoincrement=True)
    merchantId = Column(Integer, ForeignKey('merchants.merchantId'))
    bannervalidity=Column(DateTime)
    bannername=Column(String)
    choosefile=Column(Integer, ForeignKey('gallery.imageId'))
    addToHome = Column(Integer, default=0)
    status=Column(Integer,default=0)

    bannergallery = relationship('productGallery', back_populates="gallerybanner")
    bannermerchant = relationship('merchantTable', back_populates="merchantbanner")
    
class cartTable(Base):
    __tablename__ = "cart"

    cartId = Column(Integer,primary_key=True,autoincrement=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    productId = Column(Integer, ForeignKey('products.productId'))
    quantity = Column(Integer)
    merchantId = Column(Integer)
    status = Column(Integer, default=0)
    addedAt = Column(DateTime, default=datetime.now)

    cartproductrelation = relationship('productsTable', back_populates="productcartrelation")
    

class wishlistTable(Base):
    __tablename__ = "wishlist"

    wishlistId = Column(Integer,primary_key=True,autoincrement=True)
    productId = Column(Integer, ForeignKey('products.productId'))
    userId = Column(Integer, ForeignKey('user.userId'))
    status = Column(Integer, default=0)
    addedAt = Column(DateTime, default=datetime.now)

    wishlistproduct = relationship('productsTable', back_populates="productwishlist")
    wishlistuser = relationship('users', back_populates="userwishlist")


class Loyality(Base):
    __tablename__="loyality"

    loyalityId = Column(Integer,primary_key=True,autoincrement=True)
    earningCriteriaAmount = Column(Float)
    earningCriteriaPoint = Column(Float)
    minimumOrderAmount = Column(Float)
    maximumEarningPoint = Column(Float)
    expiryDuration = Column(Float)
    redemptionPoint = Column(Float)
    redemptionAmount = Column(Float)
    redemptionOrderAmount = Column(Float)
    minimumLoyalityPointForRedemption = Column(Float)


class Services(Base):
    __tablename__="services"

    id=Column(Integer,primary_key=True,autoincrement=True)
    termsandservices=Column(Text)
    aboutus=Column(Text)

class Feedback(Base):
    __tablename__="feedback"
    id=Column(Integer,primary_key=True,autoincrement=True)
    userid=Column(Integer, ForeignKey('user.userId',))
    feedback=Column(Text)
    addedat=Column(DateTime, default=datetime.now)
    
class Notification(Base):
    __tablename__="notification"
    notificationid=Column(Integer,primary_key=True,autoincrement=True)
    receiverId = Column(Integer, ForeignKey('user.userId'),nullable=True)
    sendFrom = Column(Integer, ForeignKey('user.userId'),nullable=True)
    senderStoreId = Column(Integer, nullable=True)
    receiverIdStoreId = Column(Integer, nullable=True)
    message=Column(Text)
    orderId = Column(Integer,nullable=True)
    jsonMessage = Column(JSON, nullable=True)
    clientconnectionId = Column(String(12), nullable=True)
    receiverconnectionId = Column(String(12), nullable=True)
    notificationtime = Column(DateTime,default=datetime.now)


class searchTable(Base):
    __tablename__ = "search"

    searchId = Column(Integer,primary_key=True,autoincrement=True)
    merchantId =  Column(Integer, ForeignKey('merchants.merchantId'), nullable=True)
    productId = Column(Integer, ForeignKey('products.productId'), nullable=True)
    searchTag = Column(String, nullable=False)
    addedAt = Column(DateTime, default=datetime.now)

    merchantsearch = relationship("merchantTable", back_populates="searchmerchant")
    productsearch = relationship("productsTable", back_populates="searchproduct")

#foreign_keys=[entityId], foreign_keys=[entityId], , overlaps="productsearch" , overlaps="merchantsearch"


class orderDeliveryModel(Base):
    __tablename__ = "orderDelivery"

    deliveryId = Column(Integer,primary_key=True,autoincrement=True)
    orderId = Column(Integer, ForeignKey('orders.orderId'))
    deliveryAgentId = Column(Integer, ForeignKey('user.userId'), nullable=True)
    #modeOfAssigning = Column(Integer, nullable=True) #0 manual, 1 nearest available, 2 first idle driver
    expectedArrival = Column(DateTime, nullable=True) 
    distanceToTravel = Column(Float, nullable=True)
    reachedAt = Column(DateTime,nullable=True)
    earningForDeliveryAgent = Column(Float, nullable=True)
    orderAccepted = Column(Integer,default=0) #0 not accepted, 1 accepted
    amountToBeCollected = Column(Float, nullable=True)
    addedAt = Column(DateTime, default=datetime.now)

    deliveryorderrelation = relationship("ordersTable", back_populates="orderdeliveryrelation")
    deliveryagentuser = relationship("users", back_populates="userdeliveryagent") 

class incentiveStructureModel(Base):
    __tablename__ = "incentiveStructure"

    incentiveId = Column(Integer,primary_key=True,autoincrement=True)
    earning = Column(Float)
    amountLimit = Column(Float)
    type=Column(Integer)
    addedAt = Column(DateTime, default=datetime.now)
   

class Timeslot(Base):
    __tablename__="slot"
    ShiftId=Column(Integer,primary_key=True,autoincrement=True)
    StartTime=Column(Time,nullable=True)
    EndTime=Column(Time,nullable=True)
    MaxiAmount=Column(Integer)
    addedat=Column(DateTime, default=datetime.now)

#   numberOfAgentsRequired =
#     numberOfAgentsgot =


class payments(Base):

    __tablename__ = "paymentTable"

    slNo = Column(Integer, autoincrement=True, primary_key=True)
    userId = Column(Integer)
    orderId = Column(String(255))
    oradoOrderId = Column(Integer, ForeignKey('orders.orderId'))
    recieptId = Column(String(255))
    amount = Column(String(50))
    currency = Column(String(255),default="INR")
    razorpayPaymentId = Column(String(255), default=None)
    status = Column(Integer, default=0) #0 unpaid 1 paid
    transactionTime = Column(DateTime,default=datetime.now)

    paymentorder = relationship("ordersTable", back_populates= "orderpayment")


class deliveryAgentLog(Base):

    __tablename__ = "deliveryLog"

    deliveryLogId = Column(Integer, autoincrement=True, primary_key=True)
    userId =  Column(Integer, ForeignKey('user.userId'))
    isActive = Column(Integer, default=0) #0 inactive or not started yet 1 active
    logDate = Column(Date)
    startTime = Column(DateTime, nullable=True)
    endTime =  Column(DateTime, nullable=True)
    latitude = Column(Float, nullable=True)  # Storing latitude
    longitude = Column(Float, nullable=True)
    last_update = Column(DateTime,default=datetime.now)
    shiftId = Column(Integer, nullable= True)
    completedOrders = Column(Integer, default=0)
    hoursWorked = Column(String(10))

    deliveryagentloguser = relationship("users", back_populates="userdeliveryagentlog")

class deliveryAgentPersonalData(Base):

    __tablename__ = "agentPersonalData"

    deliveryAgentPID = Column(Integer, autoincrement=True, primary_key=True)
    userId =  Column(Integer, ForeignKey('user.userId'))
    vehicleType = Column(String(255))
    vehicleNumber = Column(String(50))
    aadharCard = Column(String(50))
    panCard = Column(String(50))
    joinedOn = Column(DateTime,default=datetime.now)

    deliveryagentpersonal = relationship("users", back_populates="userdeliveryagentpersonal")

class usersearch(Base):
    __tablename__="user_search"
    
    userserchid=Column(Integer,autoincrement=True,primary_key=True)
    userId =  Column(Integer, ForeignKey('user.userId'))
    keyword=Column(String(255))

class AppFeedback(Base):
    __tablename__="appfeedback"
    appid=Column(Integer,autoincrement=True,primary_key=True)
    userId=Column(Integer, ForeignKey('user.userId'))
    appfeedback=Column(Text)
    addedat=Column(DateTime, default=datetime.now)

class Giftcard(Base):
    __tablename__="giftcard"
    cardid=Column(Integer,autoincrement=True,primary_key=True)
    name=Column(String(255))
    description=Column(Text)
    amount=Column(String(255))
    expiry = Column(DateTime)
    status = Column(Integer, default=0)
    imageId = Column(Integer, ForeignKey('gallery.imageId'))
    addedat=Column(DateTime, default=datetime.now)

    giftcardproductgallery = relationship("productGallery", back_populates="productgallerygiftcard")
    giftcardpayment = relationship("GiftCardModel", back_populates="paymentgiftcard")
    
class Cancellation(Base):

    __tablename__="policycancellation"

    cancellationId=Column(Integer,autoincrement=True,primary_key=True)
    userId=Column(Integer, ForeignKey('user.userId'))
    policyname=Column(String(255))
    status = Column(Integer, default=0)
    isactive=Column(Integer, default=0)

# 0-order placed
# 1-store status
# 2-order complete


class terminologyTable(Base):

    __tablename__="terminology"

    terminologyid=Column(Integer,autoincrement=True,primary_key=True)
    type=Column(Integer) #order,product
    subType =Column(Integer) #type of message
    terminology=Column(String(255))


# 0-fixed type
#1-dynamic type
   
class Managecities(Base):
    __tablename__="managecities"
    managecityId=Column(Integer,autoincrement=True,primary_key=True)
    name=Column(String(255))
    description=Column(String(255))
    type=Column(Integer,default=0)
    isactive=Column(Integer,default=0)

class ManagerTable(Base):
    
    __tablename__="manager"
    
    mangerId=Column(Integer,autoincrement=True,primary_key=True)
    userId=Column(Integer, ForeignKey('user.userId'))
    name=Column(String)
    
    managertableusers=relationship("users",back_populates="usersmanagertable")
    
class PreferenceTable(Base):
    
    __tablename__="preference"
    
    preferenceId=Column(Integer,autoincrement=True,primary_key=True)
    countryCode=Column(String,nullable=True)
    currency=Column(String,nullable=True)
    currencyFormatting=Column(String,nullable=True)
    timeZone=Column(String,nullable=True)
    timeFormat=Column(Time,nullable=True)
    dateFormat=Column(Date,nullable=True)
    onlineAndOfflineTax=Column(Integer,default=0)
    productShare=Column(Integer,default=0)
    shortenAddressOnMap=Column(Integer,default=0)
    deliveryAddressConfirmation=Column(Integer,default=0)
    aerialDistance=Column(Integer,default=0)
    favoriteMerchants=Column(Integer,default=0)
    autoRefund=Column(Integer,default=0)
    pickupNotifications=Column(Integer,default=0)
    orderReadyStatus=Column(Integer,default=0)
    distanceUnit=Column(Integer,default=0)
    showCommisionToMerchants=Column(Integer,default=0)
    customerRating=Column(Integer,default=0)
    hideCustomerDetailFromMerchant=Column(Integer,default=0)
    showCustomerProfileToMerchant=Column(Integer,default=0)
    showCurrencyToMerchant=Column(Integer,default=0)
    showGeofenceToMerchant=Column(Integer,default=0)
    servingRadius=Column(Integer,default=0)
    showacceptOrrejectmerchants=Column(Integer,default=0)
   
    
    
            
    

class deliveryIncentiveModel(Base):

    __tablename__ = "deliveryIncentive"

    deliveryIncentiveId = Column(Integer,autoincrement=True,primary_key=True)
    deliveryAgentId = Column(Integer)
    dateOfIncentive = Column(Date)
    amount = Column(Float)
    typeOfIncentive = Column(Integer)
    addedAt=Column(DateTime, default=datetime.now)


class geofenceTable(Base):

    __tablename__ = "geofence"

    geofenceId = Column(Integer,autoincrement=True,primary_key=True)
    geofenceName = Column(String(1000))
    points = Column(ARRAY(Float))
    isActive = Column(Integer, default=0)
    status = Column(Integer,default=0)
    addedAt = Column(DateTime, default=datetime.now)
    
class deliverysettingTable(Base):
    
    __tablename__="deliverysetting"
    
    deliverysettingId=Column(Integer,autoincrement=True,primary_key=True)
    deliveryTime=Column(Float)
    chargePerKm=Column(Float)
    freeDelivery=Column(String,nullable=True)
    defaultDeliveryManager=Column(String,nullable=True)
    externaldeliveryCharge=Column(String,nullable=True)
    trackingLineConfiguration=Column(String,nullable=True)
    deliveryCharge=Column(String,nullable=True)
    merchantWiseDeliveryCharge=Column(String,nullable=True)
    estimateTimeOfArrival=Column(String,nullable=True)
    staticsAddress=Column(String,nullable=True)
    tip=Column(String,nullable=True)


class loginTypesModel(Base):

    __tablename__ = "loginTypes"
    
    loginTypeId = Column(Integer,autoincrement=True,primary_key=True)
    google = Column(Integer, default=0)
    facebook = Column(Integer, default=0)  #0 is off 1 is on
    otp = Column(Integer, default=0)
    whatsapp = Column(Integer, default=0)
    signupUsingEmail = Column(Integer, default=0)
    signupUsingPhone = Column(Integer, default=0)
    emailVerification = Column(Integer, default=0)
    otpVerification = Column(Integer, default=0)
    reCaptcha = Column(Integer, default=0)


class orderSettingsModel(Base):

    __tablename__ = "orderSettings"

    orderSettingId = Column(Integer,autoincrement=True,primary_key=True)
    autoAccept = Column(Integer, default=0) #0 off 1 on
    orderAcceptanceTime = Column(Integer, default=0)
    allowMerchantToEdit = Column(Integer, default=0)
    allowManagerToEdit = Column(Integer, default=0)
    allowCustomersToRate = Column(Integer, default=0)
    agentOrderAcceptanceTime = Column(Integer,default=0)
    earningForAgent = Column(Float,default=0)
    autoAssignAgent = Column(Integer, default=0) #0 off 1 on

class commissionTable(Base):
    
    __tablename__="commission"
    
    commissionId=Column(Integer,autoincrement=True,primary_key=True)
    defaultCommission=Column(Integer,default=0)#0-set fixed amount,1- set percentage
    commissionValue=Column(String)
    commissiontransfer=Column(Integer,default=0)#0-set offline,1- set online


class refundModel(Base):

    __tablename__ = "refundTable"

    slNo = Column(Integer, autoincrement=True, primary_key=True)
    userId = Column(Integer)
    cancelledByUserType = Column(Integer,default=2)
    oradoOrderId =  Column(Integer, ForeignKey('orders.orderId'))
    refundId = Column(String(255))
    receiptId = Column(String(255))
    amount = Column(String(50))
    currency = Column(String(255),default="INR")
    razorpayPaymentId = Column(String(255), default=None)
    status = Column(String(255), default="refund")
    transactionTime = Column(DateTime,default=datetime.now)

    refundorder = relationship("ordersTable", back_populates="orderrefund")


class merchantReviewTable(Base):
    __tablename__ = "merchantReview" 

    merchantReviewId = Column(Integer, primary_key=True, autoincrement=True)
    merchantId = Column(Integer, ForeignKey('merchants.merchantId'))
    rating = Column(Integer,default= 0)
    comment = Column(Text)
    reviewedByUser = Column(Integer, ForeignKey('user.userId'))
    status = Column(Integer, default= 0)
    addedAt = Column(DateTime, default=datetime.now)

    reviewmerchant = relationship('merchantTable', back_populates="merchantreview")
    merchantreviewuser = relationship('users', back_populates="usermerchantreview")

class Cancellationpolicy(Base):
    __tablename__="cancellationtable"
    
    policyid= Column(Integer, primary_key=True,autoincrement=True)
    policyname=Column(String)
    orderStatus=Column(Integer,default= 0)
    allowCancellation=Column(Integer,default= 0)
    fixedCharge=Column(Float)
    percentageCharge=Column(Float)
    createdAt=Column(DateTime)
    status=Column(Integer, default= 0)
    

class agentOrderCancellationTable(Base):
    __tablename__ = "agentOrderCancellation"

    orderCancellationId = Column(Integer, primary_key=True, autoincrement=True)
    orderId = Column(Integer, ForeignKey('orders.orderId'))
    agentId = Column(Integer, ForeignKey('user.userId'))
    addedAt = Column(DateTime, default=datetime.now)


class setSchedule(Base):

    __tablename__ = "scheduledJobs"

    jobId = Column (Integer, primary_key=True, autoincrement=True)
    orderId = Column(Integer, ForeignKey('orders.orderId'))
    timeStamp = Column(DateTime)
    executionStatus = Column(Integer, default=1)


class discountMerchantTable(Base):

    __tablename__ = "discountMerchant"

    dId = Column (Integer, primary_key=True, autoincrement=True)
    discountId = Column(Integer, ForeignKey('discount.discountId'))
    merchantId =  Column(Integer, ForeignKey('merchants.merchantId'))
    status = Column(Integer, default=1)

    discounttable = relationship("discountTable", back_populates="tablediscount") 
    discountmerchants = relationship("merchantTable", back_populates="merchantdiscount")


class referralModel(Base):

    __tablename__ = "referralTable"

    referId = Column(Integer, primary_key=True, autoincrement=True)
    referralType = Column(Integer, default=0) #0 fixed 1 percent
    # referrerDiscount = Column(Float)
    # referrerMaximumDiscountValue = Column(Float)
    pointsPerReferal = Column(Float,nullable=True)
    referrerDescription = Column(Text,nullable=True)
    refereeDiscountPercentange = Column(Float,nullable=True)
    refereeMaximumDiscountValue = Column(Float,nullable=True)
    minimumOrderAmount = Column(Float,nullable=True)
    refereeDescription = Column(Text,nullable=True)
    refereeMaximumDiscountValueSwitch = Column(Integer, default=0)
    minimumOrderAmountSwitch = Column(Integer, default=0)
    refereeDescriptionSwitch = Column(Integer, default=0)

    # testColumn = Column(Integer, nullable=True)


class GiftCardModel(Base):

    __tablename__ = "giftCardPayment"

    slNo = Column(Integer, autoincrement=True, primary_key=True)
    userId = Column(Integer)
    orderId = Column(String(255))
    giftCardId = Column(Integer, ForeignKey('giftcard.cardid'))
    recieptId = Column(String(255))
    amount = Column(String(50))
    currency = Column(String(255),default="INR")
    razorpayPaymentId = Column(String(255), default=None)
    status = Column(Integer, default=0) #0 unpaid 1 paid
    transactionTime = Column(DateTime,default=datetime.now)

    paymentgiftcard = relationship("Giftcard", back_populates="giftcardpayment")
    #paymentuser = relationship("buyGiftCard", back_populates="userpayment")


class buyGiftCard(Base):

    __tablename__ = "customerGiftCard"

    customerGiftCardId = Column(Integer, autoincrement=True, primary_key=True)
    userId = Column(Integer, ForeignKey('user.userId'))
    giftCardId = Column(Integer, ForeignKey('giftcard.cardid'))

    giftcarduser = relationship("users", back_populates="usergiftcard")
    #userpayment = relationship("GiftCardModel", back_populates="paymentuser")


class referalDiscount(Base):

    __tablename__ = "referalFirstOrderDiscount"

    rfId = Column(Integer, autoincrement=True, primary_key=True)
    referalCode = Column(String(50))
