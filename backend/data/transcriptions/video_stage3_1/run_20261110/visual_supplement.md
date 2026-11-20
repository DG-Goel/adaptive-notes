# Stage 3.1 visual supplement

All raw OCR below is unverified. No transcript merging or code completion.

Stage 2 associations on new frames refer to events overlapping the targeted search window, not necessarily the individual frame.

## mortgage

### Original spoken context

> is 30. So one byte is sufficient to store the number 30 or
> anything smaller. Now based on the number of years, we calculate the number of
> payments. Note the camel notation here. I've capitalized the first letter
> of every word except the first word. So we get years
> and multiply it by months in year. Again, the code is very self-explanatory.
> Once we collect all this data, then we
> the mortgage. So we get a principal, multiply it by
> this expression, and then divide it by this other expression.
> Let's have a quick look here. Now this looks a little bit complicated, so if you want to
> download my source code, look below this video, I've attached it for you to download.
> And finally, after we calculate the mortgage, we use the number
> format class to format this value as a currency.
> So, we get our result, store it in the string, mortgage formatted,
> and print it over here. Now here we can also avoid
> declaring this variable and simply add this expression over here

### 5725.019300s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5725.019300.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5725.019300_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
float monthlyInterest = annualInterest / PERCENT / MO

System.out.print("Period (Years): ");
byte years = scanner.nextByte();
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlvInterest. numberOf
Main > main()
```
````



### 5725.019300s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5725.019300.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5725.019300_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {F l o a t m o n t h l y I n t e r e s t = a n n u a l I n t e r e s t / P E R C E N T / M O U} \\ \mathrm {S y s t e m . o u t . p r i n t} (" P e r i o d (Y e a r) : "); \\ \mathrm {b y t e y e a r s = s c a n n e r . n e x t B y t e t ()}; \\ \mathrm {i n t n u m b e r O f P a y m e n t s = y e a r s * M O N T H S _ {I N} Y E A R}; \\ \mathrm {d o u b l e m o r t g i g e = p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l v I n t e r e s t}. \mathrm {n u m b e r O f}) \\ \mathrm {M a i n} \quad \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5730.024300s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5730.024300.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5730.024300_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
float monthlyInterest = annualInterest / PERCENT / MO

System.out.print("Period (Years): ");
byte years = scanner.nextByte();
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlvInterest. numberOf
Main > main()
```
````



### 5730.024300s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5730.024300.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5730.024300_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {F l o a t m o n t h l y I n t e r e s t = a n n u a l I n t e r e s t / P E R C E N T / M O U} \\ \mathrm {S y s t e m . o u t . p r i n t} (" P e r i o d (Y e a r) : "); \\ \mathrm {b y t e y e a r s = s c a n n e r . n e x t B y t e ()}; \\ \mathrm {i n t n u m b e r O f P a y m e n t s = y e a r s * M O N T H S _ {I N} Y E A R}; \\ \mathrm {d o u b l e m o r t g e g e = p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l v I n t e r e s t}. \mathrm {n u m b e r O f}) \\ \mathrm {M a i n} > \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5735.029300s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5735.029300.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5735.029300_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
float monthlyInterest = annualInterest / PERCENT / MO

System.out.print("Period (Years): ");
byte years = scanner.nextByte();
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlvInterest. numberOf
Main > main()
```
````



### 5735.029300s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5735.029300.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5735.029300_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {F l o a t m o n t h l y I n t e r e s t = a n n u a l I n t e r e s t / P E R C E N T / M O U} \\ \mathrm {S y s t e m . o u t . p r i n t} (" P e r i o d (Y e a r) : "); \\ \mathrm {b y t e y e a r s = s c a n n e r . n e x t B y t e r}(); \\ \mathrm {i n t n u m b e r O f P a y m e n t s = y e a r s * M O N T H S _ {I N} Y E A R}; \\ \mathrm {d o u b l e m o r t g i g e = p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l v I n t e r e s t}. \mathrm {n u m b e r O f}) \\ \mathrm {M a i n} > \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5740.000933s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5740.000933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5740.000933_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
float monthlyInterest = annualInterest / PERCENT / MO

System.out.print("Period (Years): ");
byte years = scanner.nextByte();
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlvInterest. numberOf
Main > main()
```
````



### 5740.000933s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5740.000933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5740.000933_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {S y s t e m . o u t . p r i n t} (" \mathrm {P e r i o d (Y e a r s)}: "); \\ \mathrm {b y t e} \mathrm {y e a r s} = \mathrm {s c a n n e r . n e x t B y t e}(); \\ \mathrm {i n t n u m b e r O f P a y m e n t s} = \mathrm {y e a r s} * \mathrm {M O N T H S _ {I N} Y E A R}; \\ \mathrm {d o u b l e m o r t g i g e = p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l v I n t e r e s t}. \mathrm {n u m b e r O f}) \\ \mathrm {M a i n} > \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5745.005933s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5745.005933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5745.005933_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
System.out.print("Period (Years): ");
byte years = scanner.nextByte();
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlyInterest, numberOf
```

Main > main()
````



### 5745.005933s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5745.005933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5745.005933_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {S y s t e m . o u t . p r i n t} (" \mathrm {P r e i o d (Y e a r s) : "}); \\ \mathrm {b y t e y e a r s = s c a n n e r . n e x t B y t e t}(); \\ \mathrm {i n t n u m b e r O f P a y m e n t s = y e a r s * M O N T H S _ {I N} Y E A R}; \\ \mathrm {d o u b l e m o r t g e g a = p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b e r O f}) \\ \mathrm {M a i n} > \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5750.010933s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5750.010933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5750.010933_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```cpp
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlyInterest, numberOf

String mortgageFormatted = NumberFormat.getCurrencyIn
System.out.println("Mortgage: " + mortgageFormatted);
}
Main > main()
```
````



### 5750.010933s · Formula Recognition: · unresolved

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5750.010933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5750.010933_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {n u m b e r O f P a y m e n t s = y e a r * M O N T H S _ I N _ Y E A R}; \\ \mathrm {d o u b l e m o r t g a g e = p r i n c i p a l I} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b e r O f}) \\ \mathrm {S t r i n g m o r t g a g e F o r m a t t e d = N u m b e r F o r m a t t e d . g e t C u r r e n c y I n t e r e s t S y s t e m . o u t . p r i n t l n} ("M o r t g a g e: " + \mathrm {m o n t h l y} \mathrm {m o r t g a g e F o r m a t t e d}); \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {M a t h e n a l} \\ \mathrm {
````



### 5752.513433s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5752.513433.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5752.513433_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```cpp
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlyInterest, numberOf

String mortgageFormatted = NumberFormat.getCurrencyIn
System.out.println("Mortgage: " + mortgageFormatted);
}
Main > main()
```
````



### 5752.513433s · Formula Recognition: · unresolved

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5752.513433.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5752.513433_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {i n t n u m b e 0 f P a y m e n t s = y e a r * M O N T H S _ I N _ Y E A R}; \\ \mathrm {d o u b l e m o r t g e g e = p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1) + \mathrm {m o n t h l y I n t e r e s t} \\ / (\mathrm {M a t h . p o w} (1) + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b e 0 f}) \\ \mathrm {S t r i n g m o r t g e g e F o r m a t t e d = N u m b e F o r m a t t e d . g e t C u r r e n c y I n t e r e s t . S y s t e m . o u t . p r i n t l n} ("M o r t g e g e: " + \mathrm {m o n t h l y I n t e r e s t}); \\ \mathrm {M a t h . o u t . p r i n t l n} ("M o r t g e g e: " + \mathrm {m o n t h l y I n t e r e s t}); \\ \mathrm {M a t h . o u t . p r i n t l n} ("M o r t g e g e: " + \mathrm {m o n t h l y I n t e r e s t}); \\ \mathrm {M a t h . o u t . p r i n t l n} ("M o r t g e g e: " + \mathrm {m o n t h l y I n t e r e s t}); \\ \mathrm {M a t h . o u t . p r i n t l n} ("M o r t g e g e: " + \mathrm {m o n t h l y I n t e r e s t}); \\
````



### 5755.015933s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5755.015933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5755.015933_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```cpp
int numberOfPayments = years * MONTHS_IN_YEAR;

double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthly
    / (Math.pow(1 + monthlyInterest, numberOf

String mortgageFormatted = NumberFormat.getCurrencyIn
System.out.println("Mortgage: " + mortgageFormatted);
}
Main > main()
```
````



### 5755.015933s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5755.015933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5755.015933_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {int} \mathrm {n u m b e r O f P a y m e n t s} = \mathrm {y e a r s} * \mathrm {M O N T H S _ {I N} Y E A R}; \\ \mathrm {d o u b l e} \mathrm {m o r t g e g e} = \mathrm {p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b e r O f}) \\ \mathrm {S t r i n g} \mathrm {m o r t g e g e F o r m a t t e d} = \mathrm {N u m b e r F o r m a t t e d . g e t C u r r e n c y I n t e r e s t} \\ \mathrm {S y s t e m . o u t . p r i n t l n} ("M o r t g e g e: " + \mathrm {m o r t g e g e F o r m a t t e d}); \\ \mathrm {M a i n} > \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5760.020933s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5760.020933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5760.020933_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```javascript
Payments = years * MONTHS_IN_YEAR;

age = principal
* (monthlyInterest * Math.pow(1 + monthlyInterest, numberOfPa
/ (Math.pow(1 + monthlyInterest, numberOfPayments) - 1);

ageFormatted = NumberFormat.getCurrencyInstance().format(mort
)rintln("Mortgage: " + mortgageFormatted);

Main > main()
```
````



### 5760.020933s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5760.020933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5760.020933_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {P a y m e n t s} = \mathrm {y e a r s} * \mathrm {M O N T H S _ {I N} Y E A R}; \\ \mathrm {g a i e} = \mathrm {p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b l e O f P a y m e n t s}) / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b l e O f P a y m e n t s}) - 1); \\ \mathrm {g a i e F o r m a t t e d} = \mathrm {N u m b l e F o r m a t t e d . g e t C u r r e n c y I n s t a n c e}(). \mathrm {f o r m a t t (m o r t h l y I n t e r e s t)} \\ \mathrm {p r i n t l n} (" M o r t g a g e: " + \mathrm {m o r t g a g e F o r m a t t e d}); \\ \mathrm {M a i n} > \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5765.025933s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5765.025933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5765.025933_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthlyInterest)
    / (Math.pow(1 + monthlyInterest, numberOfPayment))

String mortgageFormatted = NumberFormat.getCurrencyInstance()
System.out.println("Mortgage: " + mortgageFormatted);
```

Main > main()
````



### 5765.025933s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5765.025933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5765.025933_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\text{double mortgage} = \text{principal}
$$
* (monthlyInterest * Math.pow(1 + monthlyInterest)
/ (Math.pow(1 + monthlyInterest, numberOfPayment))

String mortgageFormatted = NumberFormat.getCurrencyInstance(System.out.println("Mortgage: " + mortgageFormatted));
$$
\mathrm{Main} \quad \mathrm{main()}
$$
````



### 5770.030933s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5770.030933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5770.030933_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```javascript
mortgage = principal
  * (monthlyInterest * Math.pow(1 + monthlyInterest,
  / (Math.pow(1 + monthlyInterest, numberOfPayments))

ring mortgageFormatted = NumberFormat.getCurrencyInstance().f
stem.out.println("Mortgage: " + mortgageFormatted);

Main > main()
```
````



### 5770.030933s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5770.030933.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5770.030933_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b e r O f P a y m e n t s}) \\ \mathrm {r i n g m o n t g a l e F o r m a t t e d} = \mathrm {N u m b e r F o r m a t t e d}. \mathrm {g e t C u r r e n c y I n s t a n c e}(). f o r \\ \mathrm {s t e m . o u t}. \mathrm {p r i n l t n} ("M o r t g a g e: " + \mathrm {m o n t g a l e F o r m a t t e d}); \\ \mathrm {M a i n} \quad \mathrm {m a i n ()} \\ \end{array}
$$
````



### 5775.002567s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5775.002567.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5775.002567_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthlyInterest
    / (Math.pow(1 + monthlyInterest, numberOfPayments)

String mortgage@Formatted = NumberFormat.getCurrencyInstance()
System.out.println("Mortgage: " + mortgageFormatted);
```

Main > main()
````



### 5775.002567s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5775.002567.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5775.002567_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\text{double mortgage} = \text{principal}
$$
* (monthlyInterest * Math.pow(1 + monthlyInterest)
/ (Math.pow(1 + monthlyInterest, numberOfPayments)

String mortgage@Formatted = NumberFormat.getCurrencyInstance()
System.out.println("Mortgage: " + mortgageFormatted);

Main > main()
$$
````



### 5779.907467s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5779.907467.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5779.907467_Text.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
```java
double mortgage = principal
    * (monthlyInterest * Math.pow(1 + monthlyInterest
    / (Math.pow(1 + monthlyInterest, numberOfPayments)

String mortgageFormatted = NumberFormat.getCurrencyInstance()
System.out.println("Mortgage: " + mortgageFormatted);

Main > main()
```
````



### 5779.907467s · Formula Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\original_5779.907467.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\mortgage\crop_5779.907467_Formula.png)

Stage 2 context IDs: 365ba0502d15f7ff, c64f80e3b63a59ee, bcaf4f1fa2f84718

````text
$$
\begin{array}{l} \mathrm {d o u b l e} \mathrm {m o g t a g e} = \mathrm {p r i n c i p a l} \\ * (\mathrm {m o n t h l y I n t e r e s t} * \mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}) \\ / (\mathrm {M a t h . p o w} (1 + \mathrm {m o n t h l y I n t e r e s t}, \mathrm {n u m b e r O f P a y m e n t s}) \\ \mathrm {S t r i n g} \mathrm {m o g t a g e F o r m a t t e d} = \mathrm {N u m b e r F o r m a t t e d . g e t C u r r e n c y I n s t a n c e ()} \\ \mathrm {S y s t e m . o u t . p r i n l t n} (" M o r t g a g e: " + \mathrm {m o r t g a g e F o r m a t t e d}); \\ \mathrm {M a i n} \quad \mathrm {m a i n ()} \\ \end{array}
$$
````


## windows_path

### Original spoken context

> windows, backslash, whatever. Now,
> if you want to store this in a string, we need to escape each backslash. Let me show you.
> So, C, drive, backslash,
> now we have a problem. Java compiler thinks we're escaping the
> code here, so it thinks our string is not terminated with another
> double code. But that's not what we want. You want to add a backslash here. So
> we need to prefix our backslash with another backslash.
> Now we type windows, one more time,
> something. Let's run the program,
> so even though we have two backslashes in our code, we actually
> see one backslash in the terminal window. Another escape

### 3110.006900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3110.006900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3110.006900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Window
        String message = "Hello \"Mosh\"";
        System.out.println(message);
    }
}
```
````



### 3114.010900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3114.010900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3114.010900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "Hello \"Mosh\"";
        System.out.println(message);
    }
}
```
````



### 3118.014900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3118.014900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3118.014900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "Hello \"Mosh\"";
        System.out.println(message);
    }
}
```
````



### 3122.018900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3122.018900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3122.018900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "c:\";
        System.out.println(message);
    }
}
```
````



### 3126.022900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3126.022900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3126.022900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "c:\";
        System.out.println(message);
    }
}
```
````



### 3130.026900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3130.026900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3130.026900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "c:\"";
        System.out.println(message);
    }
}
```
````



### 3131.027900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3131.027900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3131.027900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "c:\"";
        System.out.println(message);
    }
}
```
````



### 3134.030900s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3134.030900.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3134.030900_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "c:|";
        System.out.println(message);
    }
}
```
````



### 3138.001533s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3138.001533.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3138.001533_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "c:\\";
        System.out.println(message);
    }
}
```
````



### 3142.005533s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3142.005533.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3142.005533_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public class Main {

    public static void main(String[] args) {
        // c:\Windows\...
        String message = "c:\Windows\\..|";
        System.out.println(message);
    }
}
```
````



### 3146.009533s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3146.009533.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3146.009533_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public static void main(String[] args) {
    // c:\Windows\...
    String message = "c:\Windows\...";
    System.out.println(message);
}
```

Main > main()

Main >

/Library/Java/JavaVirtualMachines/jdk-12.0.1.jdk
c:\Windows\...
```
````



### 3150.013533s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3150.013533.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3150.013533_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public static void main(String[] args) {
    // c:\Windows\...
    String message = "c:\Windows\...";
    System.out.println(message);
}
```

Main > main()

Main >

/Library/Java/JavaVirtualMachines/jdk-12.0.1.jd
c:\Windows\...
```
````



### 3151.915433s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\original_3151.915433.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path\crop_3151.915433_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
```java
public static void main(String[] args) {
    // c:\Windows\...
    String message = "c:\Windows\...";
    System.out.println(message);
}
```

Main > main()

Main >

/Library/Java/JavaVirtualMachines/jdk-12.0.1.jd
c:\Windows\...
```
````


## windows_path_literal

### Original spoken context

> windows, backslash, whatever. Now,
> if you want to store this in a string, we need to escape each backslash. Let me show you.
> So, C, drive, backslash,
> now we have a problem. Java compiler thinks we're escaping the
> code here, so it thinks our string is not terminated with another
> double code. But that's not what we want. You want to add a backslash here. So
> we need to prefix our backslash with another backslash.
> Now we type windows, one more time,
> something. Let's run the program,
> so even though we have two backslashes in our code, we actually
> see one backslash in the terminal window. Another escape

### 3146.009533s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path_literal\original_3146.009533.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path_literal\crop_3146.009533_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
String message = "c:\\Windows\\...";
````



### 3150.013533s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path_literal\original_3150.013533.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\windows_path_literal\crop_3150.013533_Text.png)

Stage 2 context IDs: 3abe89da8c0e3837

````text
String message = "c:\\Windows\\...";
````


## failed_task

### Original spoken context

> the monthly interest, so the proper way to do this

### 8775.066300s · Text Recognition: · success

[Original](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\failed_task\original_8775.066300.png) · [Crop](C:\Projects\adaptive-notes\backend\data\transcriptions\video_stage3_1\run_20261110\failed_task\crop_8775.066300_Text.png)

Stage 2 context IDs: 9ab9874fed29b258

````text
```java
}

while (true) {
    System.out.print("Annual Interest Rate: ");
    float annualInterest = scanner.nextFloat();
    if (annualInterest >= 1 && annualInterest <= 30)
        break;
    float monthlyInterest = annualInterest / PERCENT / M
}

System.out.print("Period (Years): ");
byte years = scanner.nextByte();
```
````

