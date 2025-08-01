# PEARL R Shiny Demo App

This R Shiny application demonstrates the capabilities of `bslib` and various Shiny widgets.

## Features

### bslib Components
- **Page Layout**: Uses `page_sidebar()` for modern layout
- **Cards**: Organized content in Bootstrap cards
- **Value Boxes**: Display key metrics with icons
- **Dynamic Theming**: Switch between Bootstrap themes (Bootstrap, Minty, Darkly)

### Shiny Widgets Demonstrated
- `sliderInput()` - Sample size control
- `selectInput()` - Plot type selection
- `radioButtons()` - Theme selection
- `actionButton()` - Data refresh trigger
- `plotlyOutput()` - Interactive plots
- `DTOutput()` - Data tables
- `verbatimTextOutput()` - Summary statistics

## Installation & Running

```r
# Install required packages
install.packages(c("shiny", "bslib", "DT", "plotly", "ggplot2"))

# Run the app
shiny::runApp()
```

## Features Overview

1. **Interactive Sidebar**: Controls for sample size, plot type, and theme
2. **Dynamic Plotting**: Three plot types with interactive features via plotly
3. **Real-time Updates**: Data refreshes and statistics update automatically
4. **Responsive Design**: Layout adapts to different screen sizes
5. **Theme Switching**: Live theme changes without page reload
