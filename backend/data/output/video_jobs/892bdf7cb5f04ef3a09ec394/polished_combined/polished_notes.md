# Study notes

## real exchange rate

# Relative Prices and the Real Exchange Rate

## Open Economy Overview
An **open economy** allows consumers to purchase goods **domestically** or **abroad**. The key question is: *which good is more expensive?*

## Real Exchange Rate (RER)
- The **real exchange rate** measures the relative price of domestic goods compared to foreign goods.
- **Rising RER** → domestic goods become **more expensive** relative to international goods.
- **Falling RER** → domestic goods become **cheaper** relative to foreign goods.

### Implications
1. **Higher RER**
   - Imports become relatively cheaper.
   - Exports may lose competitiveness.
2. **Lower RER**
   - Domestic consumers find imported goods relatively pricier.
   - Exports become more attractive to foreign buyers.

Understanding how the **real exchange rate** moves helps explain trade patterns and price comparisons between home and abroad.

| Item | Description |
| --- | --- |
| goes up | when the real exchange rate goes up, domestic goods become more expensive relative to international goods |
| goes down | when the real exchange rate goes down, domestic goods become cheaper relative to foreign goods |

## openness in financial market

## Investment Decision: Domestic vs. Foreign Assets

When you have **money to invest**, you must choose between **domestic assets** and **foreign assets**. To make an informed choice, you need an understanding of the **expected relative return** of domestic and foreign bonds. This comparison helps determine which market offers the better risk‑adjusted opportunity for your investment.

## dollar bond

## Investment Comparison: Dollar‑Denominated vs. British Bonds

- **Dollar bond**: Investing in a bond denominated in U.S. dollars.
- **British bond**: A bond issued in the United Kingdom that is considered **as safe as a U.S. bond**.

### Interest Rates
1. The British bond offers a **10 % interest rate**.
2. The comparable U.S. bond pays **5 % interest**.

**Key takeaway:** The British bond provides a higher return while maintaining a safety level comparable to the U.S. bond.

## interest rate

# Currency Exposure

**Currency exposure** refers to the risk that a company's cash flows, assets, or liabilities will be affected by fluctuations in foreign exchange rates. It arises when a firm conducts business across borders, holds assets denominated in foreign currencies, or has obligations payable in those currencies.

---

### Key Points
- **Types of exposure**:
  1. **Transaction exposure** – risk from actual cash flows (e.g., paying a foreign supplier).
  2. **Translation exposure** – accounting impact when consolidating foreign subsidiaries.
  3. **Economic exposure** – long‑term effect on competitive position and market value.
- **Management strategies**:
  - **Hedging** with forwards, futures, options, or swaps.
  - **Natural hedging** by matching currency inflows and outflows.
  - **Diversification** of markets and currency denominations.

---

### Practical Example
A U.S. company sells products in Europe and invoices customers in euros. If the euro weakens against the dollar before payment is received, the company will collect fewer dollars, illustrating **transaction exposure**.

---

### Why It Matters
- Impacts profitability and cash flow stability.
- Influences pricing, budgeting, and financial reporting.
- Requires continuous monitoring of exchange‑rate movements and proactive risk‑management policies.

## expected exchange rate

## Converting Foreign Bond Returns to Domestic Currency

- **Step 1:** Use the *expected exchange rate* to convert future foreign‑currency cash flows (e.g., pounds) into the domestic currency (e.g., dollars).

- **Step 2:** Calculate the foreign‑currency payoff.
  - Example: Invest **£0.8**. If the UK bond yields **10 %**, the payoff in pounds is:
    ```
    £0.8 × (1 + 0.10) = £0.88
    ```

- **Step 3:** Convert the payoff to dollars using the expected exchange rate for the next period:
    ```
    Return in $ = £0.88 ÷ (expected $/£ rate)
    ```
  This gives the **domestic‑currency return** from the UK bond.

## Comparing Domestic and Foreign Bonds

- Suppose you invest **$1** today in a U.S. bond that yields **5 %**. The dollar payoff tomorrow is:
    ```
    $1 × (1 + 0.05) = $1.05
    ```

- For the UK bond, after converting the pound payoff back to dollars (Step 3), you obtain a comparable dollar amount.

### Role of Exchange‑Rate Movements

- A higher nominal foreign‑bond yield does **not** guarantee a superior investment because exchange‑rate changes can offset the yield advantage.
  - If the pound **depreciates** by 5 % relative to the dollar, a 10 % UK‑bond return is effectively reduced by that 5 % currency loss.
  - Conversely, if the dollar **appreciates** 5 % against the pound, the investor is **indifferent** between the U.S. and UK bonds.

- **Net return** after accounting for exchange‑rate effects:
  - When the expected depreciation/appreciation exactly offsets the yield differential, both bonds deliver the same domestic return (e.g., **5 %** in the example).

## Equilibrium Condition

- In equilibrium, the **expected total return** (bond yield + exchange‑rate change) must be equal across comparable investment opportunities.  
- Therefore, investors will be indifferent between a **5 % US bond** and a **10 % UK bond** if they expect the pound to depreciate by **5 %** relative to the dollar.

## uncovered interest parity condition

# Uncovered Interest Parity (UIP) Condition

**Definition**

The **uncovered interest parity (UIP)** condition states that the expected return on a domestic asset should equal the expected return on a foreign asset when both returns are expressed in the same currency. In other words, investors should be indifferent between holding a domestic security and a foreign security that is not hedged against exchange‑rate risk.

**Formula**

```
(1 + i_d) = (1 + i_f) * E_t[ S_{t+1} / S_t ]
```
- `i_d` – nominal interest rate on the **domestic** asset.
- `i_f` – nominal interest rate on the **foreign** asset.
- `S_t` – spot exchange rate at time *t* (price of foreign currency in domestic currency).
- `E_t[ S_{t+1} ]` – expected spot exchange rate at time *t+1*.

Rearranging gives the more common linear approximation:

```
 i_d ≈ i_f + E_t[ ΔS_{t+1} / S_t ]
```
where `ΔS_{t+1}` is the expected change in the exchange rate.

**Key Implications**

1. **No Arbitrage** – If UIP holds, there is no risk‑free profit from borrowing in one currency, converting, investing abroad, and then converting back at the expected future rate.
2. **Exchange‑Rate Expectations** – The condition links interest‑rate differentials to market expectations of future exchange‑rate movements.
3. **Risk Neutrality** – UIP assumes investors are risk‑neutral with respect to exchange‑rate risk; they do not demand a risk premium.

**Assumptions**

- Perfect capital mobility.
- No transaction costs or taxes.
- Rational expectations about future exchange rates.
- Identical risk characteristics for domestic and foreign assets, aside from currency risk.

**Limitations**

- Empirical evidence often shows systematic deviations (the “forward premium puzzle”).
- Real‑world frictions such as capital controls, transaction costs, and risk aversion can invalidate UIP.

**Example**

Suppose the U.S. interest rate (`i_d`) is 4 % and the Eurozone interest rate (`i_f`) is 2 %. If investors expect the euro to **depreciate** by 1 % relative to the dollar over the next year, the expected exchange‑rate change is `E_t[ΔS_{t+1}/S_t] = -0.01`. Plugging into the linear UIP equation:

```
 i_d ≈ i_f + expected depreciation
 0.04 ≈ 0.02 - 0.01 = 0.01
```
The left‑hand side exceeds the right‑hand side, indicating that, under UIP, the dollar would be **over‑valued** or that the expected depreciation is underestimated.

---

*The uncovered interest parity condition provides a foundational link between interest rates and exchange‑rate expectations, serving as a benchmark for analyzing international financial markets.*

## interest parity condition

## Interest Parity Condition

The **interest parity condition** states that the difference between domestic and foreign interest rates is equal to the expected change in the exchange rate. It ensures that investors are indifferent between holding domestic or foreign assets when exchange‑rate expectations are taken into account.

## Exchange‑Rate Movements

- An **increase in the value of the dollar** relative to another currency is reflected by the foreign currency price moving upward. In other words, more units of the foreign currency are required to purchase one dollar.

## International Trade and Financial Markets

1. **Trade‑only regime** – Countries may permit the **international trade of goods** while keeping their **financial markets closed** to foreign investors. This isolates capital flows but allows the exchange of physical products.
2. **Open‑capital regime** – Allowing **cross‑border flows of capital and financial assets** enables investors to buy and sell securities across borders, integrating domestic and global financial markets.

## imports and exports

## Overview of the Goods‑Market Model

The **goods‑market model** is the first framework introduced in the course. It focuses on the interaction between **domestic demand** and **domestic supply** of goods, while also accounting for the role of the **rest of the world**.

### Key Points

- The model now incorporates **imports** and **exports**, reflecting a more realistic open‑economy setting.
- It revisits the **IS‑LM** framework, but the emphasis here is on the **goods market only**.
- In a **closed economy**, the distinction between *demand for domestic goods* and *domestic demand for goods* is unnecessary. In an open economy, however, this nuance becomes important.

### Economic Agents

1. **Residents** – includes households, firms, and the government. These agents **demand goods domestically**.
2. **Agents + Rest of the World** – together they **demand domestically produced goods**, encompassing both domestic consumption and foreign demand for exports.

### Implications

- Recognizing the separate demands helps clarify how **imports** (foreign‑produced goods consumed domestically) and **exports** (domestically produced goods consumed abroad) affect overall equilibrium.
- This distinction is essential for analyzing trade balances, exchange rates, and policy impacts in an open‑economy context.

## Domestic demand

## Domestic Demand

**Domestic demand** represents the total spending within an economy and is composed of three main components:

1. **Household consumption** – the goods and services purchased by households.
2. **Firm investment** – expenditures by businesses on capital goods, such as machinery, equipment, and structures.
3. **Government expenditure** – spending by government entities on public services, infrastructure, and other governmental activities.

The sum of these three elements gives the overall domestic demand:

```
Domestic Demand = Household Consumption + Firm Investment + Government Expenditure
```

### Domestic demand

## Domestic Demand Overview

- **Domestic demand** consists of:
  - Household **consumption**
  - Firm **investment**
  - Government **expenditure**

- The economy’s **behavioral functions** are limited to two core relationships:
  1. The **consumption function**
  2. The **investment function**

- While the **level of domestic demand** itself may stay constant, it no longer **determines the demand for domestically produced goods**.

## demand for domestic goods

## Domestic Demand for Goods

- **Domestic demand** in an open economy is the **domestic demand in a closed economy** minus the portion of that demand satisfied by imported inputs.
- A component of this demand comes from **foreign consumers** who purchase U.S.-produced goods; this is often referred to as **export demand**.
- When inputs are priced in a foreign currency, the **exchange rate** must be applied to convert those costs into dollars, effectively dividing the demand by the exchange rate.
- Certain goods, such as **BMWs**, represent demand for foreign‑produced items. This type of demand does **not** contribute to the production of domestic goods (e.g., it does not affect the output of four‑door cars manufactured in the U.S.).

## exports

## Key Concepts

- **Exports (x)** – The total value of domestically produced goods sold to foreign markets.
- **New Key Concept (z)** – Defined as the **foreign demand for domestically produced goods**.

These concepts are central to understanding how international trade influences a country's economy.

## China reopening leads to increased demand for commodities

# Global Trade Dynamics

## 1. Impact of China’s Reopening
- The reopening of **China** has triggered a surge in demand for various **commodities** worldwide.

## 2. Real Exchange Rate Effects
- **Depreciation of the real exchange rate** makes domestic goods **more expensive** relative to foreign goods, which **reduces demand for exports**.
- Conversely, when the **real exchange rate rises** (appreciates), **exports decrease**.
- A **real exchange depreciation** leads to **less demand for U.S. goods abroad**.

## 3. Relationship Between Exports and Imports
- **Exports** and **imports** are mirror images:
  1. **Exports** represent goods a country sells abroad.
  2. **Imports** reflect what other countries consider their **exports** to the domestic market.

## 4. Current Export Trend
- Despite the exchange‑rate dynamics, **exports are increasing** overall.

## Imports as function of domestic output

## Trade and Exchange Rate Relationships

- **Imports rise** when **domestic output** expands, reflecting higher domestic demand for foreign goods.
- **Imports also increase** when the **real exchange rate** (\(\epsilon\)) appreciates, making foreign products cheaper for domestic consumers.

| Item | Description |
| --- | --- |
| Exports | Exports decrease when the real exchange rate rises. |
| Imports | Imports increase when the real exchange rate (epsilon) rises. |

## Impact of Epsilon on Domestic Prices

- **When `epsilon` increases**, the price of **domestic goods** rises, making them more expensive relative to foreign alternatives.

## 45-degree line equilibrium concept

## Equilibrium Concept

The **45-degree line** represents the equilibrium point where `output` equals `demand`. At this intersection, the economy is in balance, indicating that the quantity produced matches the quantity desired by consumers.

## Domestic demand adjustment

## Domestic Demand and the ZZ Curve

- **Domestic demand** is obtained by subtracting imports from total demand. This adjustment shifts the demand curve **downward** and makes it **flatter**.
- The shift is **not a simple parallel translation**; the curve also **rotates**, becoming flatter at higher income levels.
- The shape of the curve depends on **domestic output** and is influenced by **foreign output**, which acts as an external parameter.
- Although foreign output affects the position of the curve, it **does not alter its slope**.
- The resulting curve, representing the equilibrium level of domestic output, is called the **ZZ curve**.

### Key Observations
1. The **ZZ curve** differs from the traditional **DD curve** in its orientation and responsiveness to income changes.
2. The most noticeable distinction is the **flattening effect** at higher income levels, reflecting the impact of import subtraction.

## multiplier

## Multiplier Effect
- The **multiplier** arises because an increase in income raises consumption, which in turn raises income again, creating a chain reaction.

## Open Economy
- The model can be extended to an **open economy**, incorporating trade and capital flows.

## Parameter \(Y^*\)
- \(Y^*\) is a crucial parameter representing the income level in the closed‑economy **IS‑LM** model.

## Trade balance zero point

## Domestic Demand and Trade Balance

- **Domestic demand for goods** refers to the demand for goods produced within the country. When domestic demand equals the demand for domestically produced goods, the **trade balance** is zero, meaning **exports exactly equal imports**. Consequently, **net exports** are also zero.

## Net Export Function

- The **net export function** is defined as:
  
  ```
  Net Exports = (Exports - Imports) / Exchange Rate
  ```

- This function is a **decreasing function of domestic output**; as domestic output rises, net exports tend to fall.

## trade deficit

# Trade Balance and Domestic Output

## Key Concepts
- **Trade Deficit**: A situation where **imports exceed exports**.
- **Trade Surplus**: A situation where **exports exceed imports**.
- **Net Exports (NX)**: The difference between a country's **exports and imports**; it **rises when the exchange rate depreciates**.
- **Domestic Output (Y)**: The level of output where **total demand equals total supply**, found by keeping the domestic demand curve and removing extra curves.
- **Demand‑Determined Model**: In the short run, **equilibrium output equals aggregate demand**.
- **Aggregate Demand**: Refers to **domestically produced goods**.
- **ZZ Curve**: Used in short‑run analysis instead of the **DD curve**.
- **Multiplier Effect**: Even with a smaller multiplier, an effect still occurs.

## Scenarios
1. **Import‑Heavy Situation**
   - The country imports more than it exports, creating a **negative balance of trade** (trade deficit).
   - Example: The equilibrium output in the model shows a trade deficit.
2. **Export‑Driven Situation**
   - Exports exceed imports, resulting in a **trade surplus**.
   - The net export function shifts **upward**, reflecting stronger export performance.

## Impact of Government Expenditure
- An increase in government spending raises output:
  1. Output rises **more than the increase in spending** but **less than it would in a closed economy**.
  2. Part of the additional consumption expenditure is directed toward **foreign goods**, so domestic demand does not increase as much.
  3. The trade deficit can emerge **from an initially balanced situation** when the extra demand leaks abroad.

## Short‑Run Equilibrium
- In the short run, **output (Y) equals aggregate demand**.
- The analysis relies on the **ZZ curve**, which captures the relationship between output and demand under the given assumptions.
- Even with a reduced multiplier, the **multiplier effect** still amplifies the impact of fiscal changes.

## Summary
- **Trade balance** hinges on the relative sizes of imports and exports.
- **Domestic output** aligns with demand when the appropriate demand curve is used.
- Fiscal policy influences output and the trade balance, with part of the stimulus potentially leaking to foreign goods, affecting the overall trade position.

## Z‑Z curve

## Impact of Export Growth on the Z‑Z Curve

- **Export increase** causes the **Z‑Z curve** to shift **upward**.
- This upward shift reflects a rise in **domestic output**.
- Consequently, **China's output** is also **increasing** as a result of higher exports.

#### Cause and Effect

```mermaid
flowchart LR
    A["Exports increasing"] --> B["Higher equilibrium output"]
```

## net exports

## Net Exports and Real Exchange Rate Appreciation

- **Ambiguity of Net Exports**: When the **real exchange rate** appreciates, the impact on **net exports** is not clear‑cut; the effect can go either way.
- **Volume Relationship**: The volume expression for net exports is *clearly increasing* in the real exchange rate.
- **Import Behavior**: If U.S. goods become more expensive relative to foreign goods, consumers tend to **import more**.
- **Key Determinants**:
  1. The **net export term** is the only component that directly depends on the exchange rate.
  2. Net exports **rise** when foreign output (**`y*`**) increases.
  3. Net exports **fall** when domestic output (**`y`**) rises, because higher domestic production raises the demand for inputs.

*In summary, an appreciation of the real exchange rate creates opposing forces on net exports: it can boost import volumes while also influencing the balance through changes in foreign and domestic output.*

## assumption

## Net Exports and Currency Appreciation

The speaker assumes that some effects are weaker than others. Consequently, **net exports decline when the currency appreciates**.

## Depreciating the exchange rate

## Net Export Function and Trade Balance

- **Move the net export function upward** to reflect a higher baseline of exports.

## Depreciation and Its Effects

- **Depreciation is expansionary** because it shifts the spending of residents and foreigners toward **domestic goods**.
- This shift **increases demand** for domestic products, which **raises output**.

## Restoring Trade Balance After Depreciation

1. **Set a target** for the desired trade balance.
2. **Adjust policy** to achieve that target, using one or more of the following tools:
   - **Reduce government expenditure** to lower overall demand for imports.
   - **Encourage export growth** to boost the trade surplus.

> *If the goal is not to increase output directly, focusing on policies that improve the trade balance—such as reducing government spending or stimulating exports—can be more effective.*

## Using Output Expansion to Improve Net Exports

- Leveraging **output expansion** can enhance net exports, as higher domestic production often leads to greater export capacity.

## currency depreciation

## Trade Imbalances and Currency Valuation

- **Large trade deficits** are observed in certain countries, such as the **United States**.
- Conversely, **large trade surpluses** occur in other nations, notably **China**.
- These opposing balances are frequently **attributed to currency undervaluation**, which makes exports cheaper and imports more expensive for the undervalued country.

## export‑driven growth

## Economic Growth Drivers

- **Export‑led expansion**: The primary engine of economic growth was the massive volume of exports, not domestic consumption.
- **China's case**: Domestic consumption remained **very low**, while **exports were massive**, driving overall output.

## Trade Balance

## Trade Balance Overview

- The **trade balance** is calculated as the **DD curve** minus the **ZZ curve**.
- Conversely, the **ZZ curve** minus the **DD curve** represents **net exports**.
- When the **DD** and **ZZ** curves are equal, **net exports equal 0**.
- **Depreciation** improves the trade balance and increases demand for domestic goods.

