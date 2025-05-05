import datetime
from pydantic import BaseModel
from typing import List,Optional
from datetime import datetime,time, date



class categoryBase(BaseModel):
    categoryName:str = ""
    categoryImage:str = ""

class subcategoryBase(BaseModel):
    subcategoryName:str = ""
    subcategoryImage:str = ""


class addressModel(BaseModel):
    addressField: str = ""
    state: str = ""
    city: str = ""
    zipCode: str = ""
    isDefault: int


class signupModel(BaseModel):
    userName: str = ""
    userEmail: str = ""
    userPhone: str = ""
    password: str = ""
    referralCode: str = ""

class adminSignupModel(BaseModel):
    userName: str = ""
    userEmail: str = ""
    userPhone: str = ""

class userEditModel(BaseModel):
    userName: str = ""
    userEmail: str = ""
    userPhone: str = ""
    password: str = ""

class emailModel(BaseModel):
    userEmail: str = ""

class otpModel(BaseModel):
    userEmail: str = ""
    OTP: str = ""

class loginModel(BaseModel):
    input: str = ""
    password: str = ""

class merchantModel(BaseModel):
    shopName: str = ""
    handledByUser: str = ""
    userEmail:str = ""
    userName:str = ""
    userPhone:str = ""
    shopEmail: str = ""
    coverImage: str = ""
    phoneNumber: str = ""
    address: str = ""
    displayAddress: str = ""
    tags: list = []
    description: str = ""
    servingRadius: int = ""
    longitude: str = ""
    latitude: str = ""
    openingTime: time 
    closingTime: time

class merchantEditModel(BaseModel):
    merchantId: str = ""
    shopName: str = ""
    handledByUser: str = ""
    shopEmail: str = ""
    coverImage: str = ""
    phoneNumber: str = ""
    address: str = ""
    displayAddress: str = ""
    tags: list = []
    description: str = ""
    servingRadius: str = ""
    longitude: str = ""
    latitude: str = ""
    openingTime: str = ""
    closingTime: str = ""
    status:str = ""
    userEmail:str = ""
    userName:str = ""
    userPhone:str = ""
    password:str = ""
    # shopStatus: str = ""


class messageModel(BaseModel):
    recieverId: int = ""
    message: str = ""

class productModel(BaseModel):
    productName: str = ""
    description: str = ""
    price: float = ""
    costPrice: float = ""
    longDescription: str = ""
    tags: list = []
    minimumQuantity: int = ""
    maximumQuantity: int = ""
    tax: list = []
    priorityOrder: int = ""
    categoryId: int = ""
    subCategoryId: int = ""
    isVeg: int = ""
    preparationTime: str = ""
    merchantId: str = ""
    images: list = []
    

class ProductReviewCreate(BaseModel):
    productId: int
    rating: int
    comment: Optional[str] = None
   

class pagination(BaseModel):
    limit: str = ""
    page: str = ""
    search: str = ""


class orderpagination(BaseModel):
    limit: str = ""
    page: str = ""
    search: str = ""
    orderStatus: str = ""
    merchantId: str = ""
    
class delivaryagentorder(BaseModel):
    limit: str = ""
    page: str = ""
    status:str=""
    orderStatus: str = "" # empty all orders 1 completed 2 dispatched 3 cancelled

class DayTime(BaseModel):
    day: str = ""  # e.g., 'Monday'
    startTime: time
    endTime: time

class productScheduleModel(BaseModel):
    isAvailable: str = ""
    orderAcceptanceTime: str = ""
    times: List[DayTime]


class productEditModel(BaseModel):
    productName: str = ""
    description: str = ""
    price: str = ""
    costPrice: str = ""
    longDescription: str = ""
    tags: list = []
    minimumQuantity: str = ""
    maximumQuantity: str = ""
    tax: list = []
    priorityOrder: str = ""
    categoryId: str = ""
    subCategoryId: str = ""
    isVeg: str = ""
    preparationTime: str = ""
    merchantId: str = ""
    images: Optional[List[int]] = []
    isAvailable: str = ""

class productScheduleEdit(BaseModel):
    
    isAvailable: str = ""
    orderAcceptanceTime: str = ""
    times: list = []

class CouponCreate(BaseModel):
    couponname:str=""                   
    typeOfCoupon:str=""   
    price:str = ""
    description:str=""
    startingdate:datetime
    endingdate:datetime
    maxValue:str=""
    maxUsers:str=""
    minOrder:str=""
    UsersCount:str=""
    allowToUseMultipleTimes:str=""
    allowLoyalityPointsRedeem:str=""
    allowLoyalityPointsEarned:str=""  
   

class CouponDetail(BaseModel):
    page:str=""
    limit:str=""

class Discount(BaseModel):
    discountType:int=""
    discountName: str=""
    description:str=""
    validfrom:datetime
    validto:datetime
    minimumOrderAmount:float = ""
    maxiamt:float=""
    discountValue: float= ""

class BannerCreate(BaseModel):
    merchantId: str =""
    bannervalidity: datetime
    bannername: str=""
    choosefile:str=""

class bannerEdit(BaseModel):
    bannervalidity: str = ""
    bannername: str=""
    choosefile:str=""
    addToHome: str = ""

class addPagination(BaseModel):
    page:str = ""
    limit:str = ""

class addbannerPagination(BaseModel):
    page:str = ""
    limit:str = ""
    isExpired: str = ""

class orderModel(BaseModel):
    productId: int = ""
    quantity: int = ""

class myOrder(BaseModel):
    productId: int = ""
    quantity: int = ""
    merchantId: int = ""

class orderBase(BaseModel):
    order: List[orderModel]
    merchantId: str = ""
    address: str = ""
    paymentMethod: str = ""
    tipAmount: float 
    deliveryMode: int
    merchantInstruction: str = ""
    deliveryInstruction: str = ""
    couponCode: str = ""
    longitude: str = ""
    latitude: str = ""


class orderPriceBase(BaseModel):
    order: List[orderModel]
    merchantId: str = ""
    deliveryMode: int
    couponCode: str = ""
    longitude: str = ""
    latitude: str = ""
    

class productPagination(BaseModel):
    limit: str = ""
    page: str = ""
    search: str = ""
    subCategory: str = ""
    category: str = ""
    isVeg: str = ""
    merchantId: str = ""
    latitude: str = ""
    longitude: str = ""

class page(BaseModel):
    limit: str = ""
    page: str = ""


class userProfileModel(BaseModel):
    userId: str = ""

class userDetailsModel(BaseModel):
    userName:str=""
    userDOB:date=None
    bankAccountNumber: str = ""
    bankAccountHolder: str = ""
    bankIfscCode: str = ""
    bankBranch: str = ""
    upiId: str = ""

class services(BaseModel):
    termsandservices: str=""
    aboutus: str=""
    
class  LocationRequest(BaseModel):
    address:str=""
    
class GeocodeResult(BaseModel):
    formatted_address: str=""
    latitude: float=""
    longitude: float=""
    distance_to_fixed_point: float=""
    
class feedback(BaseModel):
    feedback:str=""
    
class notification(BaseModel):
    userid:str=""
    message:str=""
    usertype:str=""
    typeofnotification:str=""
    
class notificationcreate(BaseModel):
    notificationid:str=""

class TaxModel(BaseModel):
    taxName: str = ""
    tax: str = ""
    taxType: str = "" # 1 price 2 percentage
    ApplicableOn: str = ""
    differentiate: int = 0

class TaxEditModel(BaseModel):
    taxName: str = ""
    tax: str = ""
    taxType: str = "" # 1 price 2 percentage
    ApplicableOn: str = ""
    status: str = ""
    differentiate: str = ""


class loyalityModel(BaseModel):
    earningCriteriaAmount: str = ""
    earningCriteriaPoint: str = ""
    minimumOrderAmount: str = ""
    maximumEarningPoint: str = ""
    expiryDuration: str = ""
    redemptionPoint: str = ""
    redemptionAmount: str = ""
    redemptionOrderAmount: str = ""
    minimumLoyalityPointForRedemption: str = ""


class adminBase(BaseModel):
    startDate: str = ""
    endDate: str = ""

class SalesData(BaseModel):
    date: date
    total_sales: float

class orderGraph(BaseModel):
    date: date
    total_orders: int

class userLoc(BaseModel):
    latitude: float = ""
    longitude: float = ""


class assignOrderModel(BaseModel):
    deliveryAgent: str = ""
    modeOfAssigning: int = ""
    orderId: int = ""
    deliveryAgentEarning: float = ""
    merchantId: str = ""

class deliveryboyAvailability(BaseModel):
    day: date = "" #delivery agents who booked slot for the day will be shown
    isActive: str = "" #delivery agents who are active at this time
    limit: str = ""
    page: str = ""
    merchantId: str = "" #to find the closest drivers
   
    # search: str = ""
    
class incentive(BaseModel):
    earning: str=""
    amountlimit:str=""
    type:str=""
class timeslot(BaseModel):
    starttime:time
    endtime:time
    maxiamount:int=""
    
class edittime(BaseModel):
    starttime:str=""
    endtime:str=""
    maxiamount:str=""
    
class deliveryagentpersonaldata(BaseModel):
    userId : str= ""
    vehicletype :str=""
    vehiclenumber :str=""
    aadharcard :str=""
    pancard :str=""
    
class acceptOrderModel(BaseModel):
    orderId: int = ""
    longitude: str = ""
    latitude: str = ""


class paymentModel(BaseModel):
    amount: float = ""
    oradoOrderId: int = ""


class verifyPayment(BaseModel):
    razorpay_order_id:str = ""
    razorpay_payment_id: str = ""
    razorpay_signature: str = ""   


class chooseshiftmodel(BaseModel):
    shiftId: int = ""
    shiftdate: date


class deliveredModel(BaseModel):
    otp: str = ""
    orderId: str = ""
    
class keyword(BaseModel):
    keyword:str=""
    
class giftcard(BaseModel):
    name:str=""
    description:str=""
    amount:str=""
    imageId :str=""
    expiry: datetime
    
class merchantpanel(BaseModel):
    startdate:str=""
    enddate:str=""
    merchantId:str=""
   
   
class merchantproductPagination(BaseModel):
    limit: str = ""
    page: str = ""
    search: str = ""

class cancellation(BaseModel):
    policyname:str=""
    isactive:str=""

class terminology(BaseModel):
    type:int=""
    subType: int = ""
    terminology:str=""

class terminologyEdit(BaseModel):
    terminology: str = ""

class datemodel(BaseModel):
    year: str = ""
    month: str = ""

class managecity(BaseModel):
    name: str=""
    description: str=""
    type: int=""
    isactive: str=""
    
    yearMonth: str = ""

class PaymentRequest(BaseModel):
    email: str
    password: str
    amount: float
    currency: str  
    
class managermodel(BaseModel):
    name: str=""
    username:str=""
    userEmail :str=""
    userPhone :str=""
    password :str=""

class datemo(BaseModel):   
    yearMonth: str = ""
    merchantId: str = ""
   

class searchModel(BaseModel):
    search: str = ""
    longitude: str = ""
    latitude: str = ""
    isVeg: str = ""
    subCategory: str = ""
    category: str = ""
  

class editCartModel(BaseModel):
    quantity: int = ""


class geofenceCreate(BaseModel):
    geofenceName: str = ""
    points: list = []


class geofenceEdit(BaseModel):
    geofenceName: str = ""
    points: list = []
    isActive: str = ""


class sendCoordinates(BaseModel):
    latitude: float
    longitude: float
    
class prefernce(BaseModel):
    countryCode:str=""
    currency:str=""
    currencyFormatting:str=""
    timeZone:str=""
    timeFormat:time=""
    dateFormat:date=""
    onlineAndOfflineTax:int=""
    productShare:int=""
    shortenAddressOnMap:int=""
    deliveryAddressConfirmation:int=""
    aerialDistance:int=""
    favoriteMerchants:int=""
    autoRefund:int=""
    pickupNotifications:int=""
    orderReadyStatus:int=""
    distanceUnit:int=""
    showCommisionToMerchants:int=""
    customerRating:int=""
    hideCustomerDetailFromMerchant:int=""
    showCustomerProfileToMerchant:int=""
    showCurrencyToMerchant:int=""
    showGeofenceToMerchant:int=""
    showacceptOrrejectmerchants:int=""
    
class deliverysettings(BaseModel):
    
    
    deliveryTime:str=""
    chargePerKm:str=""
    freeDelivery:str=""
    defaultDeliveryManager:str=""
    externaldeliveryCharge:str=""
    trackingLineConfiguration:str=""
    deliveryCharge:str=""
    merchantWiseDeliveryCharge:str=""
    staticsAddress:str=""
    tip:str=""


class loginTypeBase(BaseModel):
    google: str = ""
    facebook: str = ""
    otp: str = ""
    whatsapp: str = ""
    signupUsingEmail: str = ""
    signupUsingPhone: str = ""
    emailVerification: str = ""
    otpVerification: str = ""
    reCaptcha: str = ""

class orderSettingBase(BaseModel):
    autoAccept: str = ""
    orderAcceptanceTime: str = ""
    allowMerchantToEdit: str = ""
    allowManagerToEdit: str = ""
    allowCustomersToRate: str = ""


class ordereditModel(BaseModel):
    productId: str = ""
    quantity: str = ""

class editOrderModel(BaseModel):
     
    order: List[ordereditModel]
    latitude: str = ""
    longitude: str = ""
    address: str = ""


class cartBase(BaseModel):
    cartId: list = []
    merchantId: str = ""
    paymentMethod: str = ""
    tipAmount: float 
    deliveryMode: int
    merchantInstruction: str = ""
    deliveryInstruction: str = ""
    couponCode: str = ""
    longitude: str = ""
    latitude: str = ""
    address: str = ""


class viewCartBase(BaseModel):
    latitude: str = ""
    longitude: str = ""

class commission(BaseModel):
    defaultCommission:str=""
    commissionValue:str=""
    commissiontransfer:str=""


class refundMod(BaseModel):
    paymentId:str = ""


class merchantReviewCreate(BaseModel):
    merchantId: int
    rating: int
    comment: str = ""
    
class cancellationpolicy(BaseModel):
    policyname:str=""
    orderStatus:int
    allowCancellation:int
    fixedcharge:float
    percentageCharge:float
    createdAt:datetime
    status:int
    
class editdiscount(BaseModel):
    discountType:str=""
    discountName: str=""
    description:str=""
    validfrom:str = ""
    validto:str = ""
    minimumOrderAmount:str = ""
    maxiamt:str=""
    discountValue: str = ""


class assigndiscountmodel(BaseModel):
    discountId: int = ""
    merchantId: list = []

class referbase(BaseModel):
    referralType:str = ""
    # referrerDiscount:str = ""
    # referrerMaximumDiscountValue:str = ""
    pointsPerReferal:str = ""
    referrerDescription:str = ""
    refereeDiscountPercentange:str = ""
    refereeMaximumDiscountValue:str = ""
    minimumOrderAmount:str = ""
    refereeDescription:str = ""
    refereeMaximumDiscountValueSwitch:str = ""
    minimumOrderAmountSwitch:str = ""
    refereeDescriptionSwitch:str = ""


class merchantonboarding(BaseModel):
    shopName: str = ""
    shopEmail: str = ""
    coverImage: str = ""
    phoneNumber: str = ""
    address: str = ""
    displayAddress: str = ""
    tags: list = []
    description: str = ""
    servingRadius: int = ""
    longitude: str = ""
    latitude: str = ""
    openingTime: time 
    closingTime: time


class deleteproductmodel(BaseModel):
    merchantId: str = ""


class merchantEditMerchant(BaseModel):
    merchantId: str = ""
    shopName: str = ""
    shopEmail: str = ""
    coverImage: str = ""
    phoneNumber: str = ""
    address: str = ""
    displayAddress: str = ""
    tags: list = []
    description: str = ""
    servingRadius: str = ""
    longitude: str = ""
    latitude: str = ""
    openingTime: str = ""
    closingTime: str = ""
    status:str = ""
    shopStatus: str = ""