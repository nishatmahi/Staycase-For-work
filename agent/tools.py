from langchain_core.tools import tool
from pydantic import BaseModel, Field

class SearchPropertiesInput(BaseModel):
    location: str = Field(description="The city or region to search in (e.g., Cox's Bazar).")
    nights: int = Field(description="Number of nights for the stay.")
    guests: int = Field(description="Number of guests.")

@tool("search_available_properties", args_schema=SearchPropertiesInput)
def search_available_properties(location: str, nights: int, guests: int) -> list[dict]:
    """
    Search for available properties based on location, dates, and number of guests.
    """
    # Mock implementation
    return [
        {"id": 1, "name": "Sea View Villa", "price_per_night": 4500, "currency": "BDT"},
        {"id": 2, "name": "Beachfront Condo", "price_per_night": 6000, "currency": "BDT"}
    ]

class GetListingDetailsInput(BaseModel):
    property_id: int = Field(description="The unique identifier of the property.")

@tool("get_listing_details", args_schema=GetListingDetailsInput)
def get_listing_details(property_id: int) -> dict:
    """
    Get detailed information about a specific property by its ID.
    """
    # Mock implementation
    return {
        "id": property_id,
        "description": "A beautiful property with amazing views.",
        "amenities": ["WiFi", "AC", "Pool"],
        "house_rules": "No smoking indoors."
    }

class CreateBookingInput(BaseModel):
    property_id: int = Field(description="The ID of the property to book.")
    check_in_date: str = Field(description="Check-in date in YYYY-MM-DD format.")
    nights: int = Field(description="Number of nights to book.")
    guests: int = Field(description="Number of guests.")

@tool("create_booking", args_schema=CreateBookingInput)
def create_booking(property_id: int, check_in_date: str, nights: int, guests: int) -> dict:
    """
    Create a booking for a specific property.
    """
    # Mock implementation
    return {
        "booking_id": "BK-98765",
        "status": "confirmed",
        "total_price": 9000,
        "currency": "BDT"
    }

tools_list = [search_available_properties, get_listing_details, create_booking]
