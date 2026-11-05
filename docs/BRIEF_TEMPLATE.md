# Project Brief: <App name>

> This file is what se-agent reads. Keep it under about 4,000 characters (~700 words).
> Replace every <...>. Delete these quote lines. Copy `examples/water-tracker.md` for a worked example.

## What we want
An online wishlist database for clothing that updates with sale and stock prices. The main problem is shoppers are struggling to keep track of clothing they find across multiple websites, and it could lead to missing the price drop.

## Users
Laptop/Desktop/Phone Browser
Can be accessed daily
Accessibility: increase text size, text to speech, icons and images

## Must do   (numbered; each one testable)
1. Create User Profile with Log in feature
2. Store items and their links
3. Organization feature for stored items (such as folders)

## Should do   (if time allows)
- Clothes recommendation for the users.
- Alert when size is in stock
- Alert when item is on sale
- Compare prices across multiple vendors

## Constraints
- Platform / technology: Three HTML pages (login,  explore, and MyClothes), no backend, no build step
- Data: Stored locally; pulls price information from websites
- Cost: any AI feature must cost less than $0.01
- Accessibility / privacy / legal: No personal identifiable information should be stored

## Out of scope (so nobody builds it by accident)
Password encryption, synching devices, making recommendations

## Quality expectations
Include unit-testable logic kept separate from the page display code.

## Acceptance criteria
- Saving an item of clothes adds it to MyClothes
- MyClothes is organized by clothing item or style
- Shows the price across different sellers

## Open questions
We do not know the official price, but live updates may increase the cost per request over a static database
