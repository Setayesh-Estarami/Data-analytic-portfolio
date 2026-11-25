/*
    Project : Food Delivery Platform Analytics
    Script  : 01_create_schema.sql
    Purpose : Create the FoodDeliveryDB database, tables, constraints and indexes
*/

-- =====================================================
-- 1. Database
-- =====================================================
IF DB_ID(N'FoodDeliveryDB') IS NULL
    CREATE DATABASE FoodDeliveryDB;
GO

USE FoodDeliveryDB;
GO

-- =====================================================
-- 2. Drop tables 
-- =====================================================
DROP TABLE IF EXISTS dbo.Reviews;
DROP TABLE IF EXISTS dbo.Deliveries;
DROP TABLE IF EXISTS dbo.OrderItems;
DROP TABLE IF EXISTS dbo.Orders;
DROP TABLE IF EXISTS dbo.Promotions;
DROP TABLE IF EXISTS dbo.MenuItems;
DROP TABLE IF EXISTS dbo.Restaurants;
DROP TABLE IF EXISTS dbo.Couriers;
DROP TABLE IF EXISTS dbo.Customers;
DROP TABLE IF EXISTS dbo.Cuisines;
DROP TABLE IF EXISTS dbo.Cities;
GO

-- =====================================================
-- 3. Lookup tables
-- =====================================================
CREATE TABLE dbo.Cities (
    CityID      INT IDENTITY(1,1) CONSTRAINT PK_Cities PRIMARY KEY,
    CityName    NVARCHAR(100) NOT NULL CONSTRAINT UQ_Cities_Name UNIQUE
);

CREATE TABLE dbo.Cuisines (
    CuisineID   INT IDENTITY(1,1) CONSTRAINT PK_Cuisines PRIMARY KEY,
    CuisineName NVARCHAR(50) NOT NULL CONSTRAINT UQ_Cuisines_Name UNIQUE
);
GO

-- =====================================================
-- 4. Core entities
-- =====================================================
CREATE TABLE dbo.Customers (
    CustomerID    INT IDENTITY(1,1) CONSTRAINT PK_Customers PRIMARY KEY,
    FullName      NVARCHAR(100) NOT NULL,
    Email         NVARCHAR(150) NOT NULL CONSTRAINT UQ_Customers_Email UNIQUE,
    Phone         NVARCHAR(20)  NULL,
    CityID        INT NOT NULL CONSTRAINT FK_Customers_Cities REFERENCES dbo.Cities(CityID),
    RegisteredAt  DATETIME2(0) NOT NULL CONSTRAINT DF_Customers_RegisteredAt DEFAULT SYSDATETIME(),
    IsActive      BIT NOT NULL CONSTRAINT DF_Customers_IsActive DEFAULT 1
);

CREATE TABLE dbo.Restaurants (
    RestaurantID   INT IDENTITY(1,1) CONSTRAINT PK_Restaurants PRIMARY KEY,
    RestaurantName NVARCHAR(150) NOT NULL,
    CuisineID      INT NOT NULL CONSTRAINT FK_Restaurants_Cuisines REFERENCES dbo.Cuisines(CuisineID),
    CityID         INT NOT NULL CONSTRAINT FK_Restaurants_Cities REFERENCES dbo.Cities(CityID),
    JoinedAt       DATE NOT NULL CONSTRAINT DF_Restaurants_JoinedAt DEFAULT CAST(SYSDATETIME() AS DATE),
    IsActive       BIT NOT NULL CONSTRAINT DF_Restaurants_IsActive DEFAULT 1
);

CREATE TABLE dbo.MenuItems (
    MenuItemID    INT IDENTITY(1,1) CONSTRAINT PK_MenuItems PRIMARY KEY,
    RestaurantID  INT NOT NULL CONSTRAINT FK_MenuItems_Restaurants REFERENCES dbo.Restaurants(RestaurantID),
    ItemName      NVARCHAR(150) NOT NULL,
    Price         DECIMAL(10,2) NOT NULL CONSTRAINT CHK_MenuItems_Price CHECK (Price > 0),
    IsAvailable   BIT NOT NULL CONSTRAINT DF_MenuItems_IsAvailable DEFAULT 1,
    CONSTRAINT UQ_MenuItems_Restaurant_Item UNIQUE (RestaurantID, ItemName)
);

CREATE TABLE dbo.Couriers (
    CourierID   INT IDENTITY(1,1) CONSTRAINT PK_Couriers PRIMARY KEY,
    FullName    NVARCHAR(100) NOT NULL,
    Phone       NVARCHAR(20)  NULL,
    CityID      INT NOT NULL CONSTRAINT FK_Couriers_Cities REFERENCES dbo.Cities(CityID),
    HiredAt     DATE NOT NULL CONSTRAINT DF_Couriers_HiredAt DEFAULT CAST(SYSDATETIME() AS DATE),
    IsActive    BIT NOT NULL CONSTRAINT DF_Couriers_IsActive DEFAULT 1
);

CREATE TABLE dbo.Promotions (
    PromotionID    INT IDENTITY(1,1) CONSTRAINT PK_Promotions PRIMARY KEY,
    PromoCode      NVARCHAR(30) NOT NULL CONSTRAINT UQ_Promotions_Code UNIQUE,
    DiscountType   NVARCHAR(10) NOT NULL CONSTRAINT CHK_Promotions_Type CHECK (DiscountType IN (N'Percent', N'Fixed')),
    DiscountValue  DECIMAL(10,2) NOT NULL CONSTRAINT CHK_Promotions_Value CHECK (DiscountValue > 0),
    StartDate      DATE NOT NULL,
    EndDate        DATE NOT NULL,
    CONSTRAINT CHK_Promotions_Dates CHECK (EndDate >= StartDate)
);
GO

-- =====================================================
-- 5. Orders and related tables
-- =====================================================
CREATE TABLE dbo.Orders (
    OrderID         INT IDENTITY(1,1) CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerID      INT NOT NULL CONSTRAINT FK_Orders_Customers REFERENCES dbo.Customers(CustomerID),
    RestaurantID    INT NOT NULL CONSTRAINT FK_Orders_Restaurants REFERENCES dbo.Restaurants(RestaurantID),
    PromotionID     INT NULL CONSTRAINT FK_Orders_Promotions REFERENCES dbo.Promotions(PromotionID),
    OrderDate       DATETIME2(0) NOT NULL,
    OrderStatus     NVARCHAR(20) NOT NULL
                    CONSTRAINT CHK_Orders_Status CHECK (OrderStatus IN (N'Placed', N'Delivered', N'Cancelled')),
    PaymentMethod   NVARCHAR(20) NOT NULL
                    CONSTRAINT CHK_Orders_Payment CHECK (PaymentMethod IN (N'Card', N'Cash', N'Wallet')),
    DeliveryFee     DECIMAL(10,2) NOT NULL CONSTRAINT DF_Orders_DeliveryFee DEFAULT 0
                    CONSTRAINT CHK_Orders_DeliveryFee CHECK (DeliveryFee >= 0),
    DiscountAmount  DECIMAL(10,2) NOT NULL CONSTRAINT DF_Orders_Discount DEFAULT 0
                    CONSTRAINT CHK_Orders_Discount CHECK (DiscountAmount >= 0)
);

CREATE TABLE dbo.OrderItems (
    OrderItemID  INT IDENTITY(1,1) CONSTRAINT PK_OrderItems PRIMARY KEY,
    OrderID      INT NOT NULL CONSTRAINT FK_OrderItems_Orders REFERENCES dbo.Orders(OrderID) ON DELETE CASCADE,
    MenuItemID   INT NOT NULL CONSTRAINT FK_OrderItems_MenuItems REFERENCES dbo.MenuItems(MenuItemID),
    Quantity     SMALLINT NOT NULL CONSTRAINT CHK_OrderItems_Qty CHECK (Quantity > 0),
    UnitPrice    DECIMAL(10,2) NOT NULL CONSTRAINT CHK_OrderItems_Price CHECK (UnitPrice > 0),  -- price at time of order
    LineTotal    AS (Quantity * UnitPrice) PERSISTED,
    CONSTRAINT UQ_OrderItems_Order_Item UNIQUE (OrderID, MenuItemID)
);

CREATE TABLE dbo.Deliveries (
    DeliveryID    INT IDENTITY(1,1) CONSTRAINT PK_Deliveries PRIMARY KEY,
    OrderID       INT NOT NULL CONSTRAINT UQ_Deliveries_Order UNIQUE
                  CONSTRAINT FK_Deliveries_Orders REFERENCES dbo.Orders(OrderID) ON DELETE CASCADE,
    CourierID     INT NOT NULL CONSTRAINT FK_Deliveries_Couriers REFERENCES dbo.Couriers(CourierID),
    PickedUpAt    DATETIME2(0) NOT NULL,
    DeliveredAt   DATETIME2(0) NOT NULL,
    DistanceKm    DECIMAL(5,2) NULL CONSTRAINT CHK_Deliveries_Distance CHECK (DistanceKm >= 0),
    CONSTRAINT CHK_Deliveries_Times CHECK (DeliveredAt >= PickedUpAt)
);

CREATE TABLE dbo.Reviews (
    ReviewID     INT IDENTITY(1,1) CONSTRAINT PK_Reviews PRIMARY KEY,
    OrderID      INT NOT NULL CONSTRAINT UQ_Reviews_Order UNIQUE
                 CONSTRAINT FK_Reviews_Orders REFERENCES dbo.Orders(OrderID) ON DELETE CASCADE,
    CustomerID   INT NOT NULL CONSTRAINT FK_Reviews_Customers REFERENCES dbo.Customers(CustomerID),
    Rating       TINYINT NOT NULL CONSTRAINT CHK_Reviews_Rating CHECK (Rating BETWEEN 1 AND 5),
    Comment      NVARCHAR(500) NULL,
    ReviewedAt   DATETIME2(0) NOT NULL
);
GO

-- =====================================================
-- 6. Indexes for common analysis queries
-- =====================================================
CREATE NONCLUSTERED INDEX IX_Orders_CustomerID   ON dbo.Orders (CustomerID);
CREATE NONCLUSTERED INDEX IX_Orders_RestaurantID ON dbo.Orders (RestaurantID);
CREATE NONCLUSTERED INDEX IX_Orders_OrderDate    ON dbo.Orders (OrderDate);
CREATE NONCLUSTERED INDEX IX_OrderItems_MenuItem ON dbo.OrderItems (MenuItemID);
CREATE NONCLUSTERED INDEX IX_Deliveries_Courier  ON dbo.Deliveries (CourierID);
CREATE NONCLUSTERED INDEX IX_MenuItems_Restaurant ON dbo.MenuItems (RestaurantID);
GO

PRINT N'FoodDeliveryDB schema created successfully.';
GO