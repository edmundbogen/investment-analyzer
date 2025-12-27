// Investment Property Analyzer - Calculator & Form Handler
// Edmund Bogen Team

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const form = document.getElementById('investmentForm');
    const steps = document.querySelectorAll('.form-step');
    const progressSteps = document.querySelectorAll('.step');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitBtn');
    const numUnitsInput = document.getElementById('numUnits');

    let currentStep = 1;
    const totalSteps = 6;

    // Initialize
    updateNavigation();
    setupEventListeners();
    calculateAll();

    // Setup all event listeners
    function setupEventListeners() {
        // Navigation buttons
        prevBtn.addEventListener('click', () => navigateStep(-1));
        nextBtn.addEventListener('click', () => navigateStep(1));

        // Form submission
        form.addEventListener('submit', handleSubmit);

        // Number of units change
        numUnitsInput.addEventListener('change', updateUnitRentFields);

        // All input fields for real-time calculation
        const inputs = form.querySelectorAll('input, select');
        inputs.forEach(input => {
            input.addEventListener('input', debounce(calculateAll, 300));
            input.addEventListener('change', calculateAll);
        });
    }

    // Debounce function for performance
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Navigation between steps
    function navigateStep(direction) {
        const newStep = currentStep + direction;

        // Validate current step before moving forward
        if (direction > 0 && !validateStep(currentStep)) {
            return;
        }

        if (newStep >= 1 && newStep <= totalSteps) {
            currentStep = newStep;
            updateStepDisplay();
            updateNavigation();

            // Calculate and update summary when reaching step 6
            if (currentStep === 6) {
                calculateAll();
                updateSummary();
            }

            // Scroll to top of form
            form.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    // Update step display
    function updateStepDisplay() {
        steps.forEach((step, index) => {
            step.classList.remove('active');
            if (index + 1 === currentStep) {
                step.classList.add('active');
            }
        });

        progressSteps.forEach((step, index) => {
            step.classList.remove('active', 'completed');
            if (index + 1 === currentStep) {
                step.classList.add('active');
            } else if (index + 1 < currentStep) {
                step.classList.add('completed');
            }
        });
    }

    // Update navigation buttons
    function updateNavigation() {
        prevBtn.disabled = currentStep === 1;

        if (currentStep === totalSteps) {
            nextBtn.style.display = 'none';
        } else {
            nextBtn.style.display = 'flex';
        }
    }

    // Validate current step
    function validateStep(step) {
        const currentStepEl = document.querySelector(`.form-step[data-step="${step}"]`);
        const requiredInputs = currentStepEl.querySelectorAll('[required]');
        let isValid = true;

        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.classList.add('error');
                input.addEventListener('input', function removeError() {
                    input.classList.remove('error');
                    input.removeEventListener('input', removeError);
                }, { once: true });
            }
        });

        if (!isValid) {
            alert('Please fill in all required fields before continuing.');
        }

        return isValid;
    }

    // Update unit rent fields based on number of units
    function updateUnitRentFields() {
        const numUnits = parseInt(numUnitsInput.value) || 1;
        const container = document.getElementById('unitRents');

        // Clear existing fields except the first one
        container.innerHTML = '';

        for (let i = 1; i <= numUnits; i++) {
            const fieldHtml = `
                <div class="form-group">
                    <label for="unit${i}Rent">Unit ${i} Monthly Rent ${i === 1 ? '*' : ''}</label>
                    <div class="input-prefix">
                        <span>$</span>
                        <input type="number" id="unit${i}Rent" name="unit${i}Rent" ${i === 1 ? 'required' : ''} min="0" placeholder="1,950">
                    </div>
                </div>
            `;
            container.insertAdjacentHTML('beforeend', fieldHtml);
        }

        // Re-add event listeners to new fields
        container.querySelectorAll('input').forEach(input => {
            input.addEventListener('input', debounce(calculateAll, 300));
            input.addEventListener('change', calculateAll);
        });
    }

    // Get form values as numbers
    function getNum(id, defaultVal = 0) {
        const el = document.getElementById(id);
        return el ? (parseFloat(el.value) || defaultVal) : defaultVal;
    }

    // Format currency
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    // Format percentage
    function formatPercent(value) {
        return (value * 100).toFixed(2) + '%';
    }

    // Calculate all values
    function calculateAll() {
        // Get input values
        const purchasePrice = getNum('purchasePrice');
        const arv = getNum('arv') || purchasePrice;
        const rehabCosts = getNum('rehabCosts');
        const closingCosts = getNum('closingCosts');

        // Calculate gross rent
        const numUnits = parseInt(getNum('numUnits', 1));
        let grossRentMonthly = 0;
        for (let i = 1; i <= numUnits; i++) {
            grossRentMonthly += getNum(`unit${i}Rent`);
        }
        const grossRentAnnual = grossRentMonthly * 12;

        // Vacancy and credit loss
        const vacancyRate = getNum('vacancyRate') / 100;
        const creditLoss = getNum('creditLoss') / 100;
        const vacancyLoss = grossRentMonthly * vacancyRate;
        const creditLossAmount = grossRentMonthly * creditLoss;

        // Other income
        const otherIncomeMonthly = getNum('laundryIncome') + getNum('parkingIncome') +
                                   getNum('petFees') + getNum('otherIncome');

        // Effective gross income
        const effectiveIncomeMonthly = grossRentMonthly - vacancyLoss - creditLossAmount + otherIncomeMonthly;
        const effectiveIncomeAnnual = effectiveIncomeMonthly * 12;

        // Operating expenses
        const propertyTaxes = getNum('propertyTaxes');
        const insurance = getNum('insurance');
        const propertyMgmtRate = getNum('propertyMgmt') / 100;
        const propertyMgmt = grossRentMonthly * propertyMgmtRate;
        const repairsRate = getNum('repairs') / 100;
        const repairs = grossRentMonthly * repairsRate;
        const capexRate = getNum('capex') / 100;
        const capex = grossRentMonthly * capexRate;
        const utilities = getNum('utilities');
        const waterSewer = getNum('waterSewer');
        const trash = getNum('trash');
        const lawnCare = getNum('lawnCare');
        const hoaFees = getNum('hoaFees');
        const pestControl = getNum('pestControl');
        const otherExpenses = getNum('otherExpenses');

        const totalExpensesMonthly = propertyTaxes + insurance + propertyMgmt + repairs + capex +
                                      utilities + waterSewer + trash + lawnCare + hoaFees +
                                      pestControl + otherExpenses;
        const totalExpensesAnnual = totalExpensesMonthly * 12;

        // NOI
        const noiMonthly = effectiveIncomeMonthly - totalExpensesMonthly;
        const noiAnnual = noiMonthly * 12;

        // Financing
        const downPaymentPercent = getNum('downPaymentPercent') / 100;
        const interestRate = getNum('interestRate') / 100;
        const loanTermYears = getNum('loanTerm');

        const downPayment = purchasePrice * downPaymentPercent;
        const loanAmount = purchasePrice - downPayment;

        // Monthly mortgage payment (P&I)
        const monthlyRate = interestRate / 12;
        const numPayments = loanTermYears * 12;
        let monthlyPayment = 0;
        if (loanAmount > 0 && monthlyRate > 0) {
            monthlyPayment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
                            (Math.pow(1 + monthlyRate, numPayments) - 1);
        }
        const annualDebtService = monthlyPayment * 12;

        // Total cash needed
        const totalCashNeeded = downPayment + closingCosts + rehabCosts;

        // Cash flow
        const monthlyCashFlow = noiMonthly - monthlyPayment;
        const annualCashFlow = monthlyCashFlow * 12;

        // Key metrics
        const capRate = purchasePrice > 0 ? noiAnnual / purchasePrice : 0;
        const cashOnCash = totalCashNeeded > 0 ? annualCashFlow / totalCashNeeded : 0;
        const dscr = annualDebtService > 0 ? noiAnnual / annualDebtService : 0;
        const grm = grossRentAnnual > 0 ? purchasePrice / grossRentAnnual : 0;
        const onePercentRule = purchasePrice > 0 ? grossRentMonthly / purchasePrice : 0;
        const twoPercentRule = purchasePrice > 0 ? (grossRentMonthly / purchasePrice) >= 0.02 : false;
        const expenseRatio = grossRentMonthly > 0 ? totalExpensesMonthly / grossRentMonthly : 0;
        const rule70Max = (arv * 0.7) - rehabCosts;

        // Update display fields
        updateElement('grossRentMonthly', formatCurrency(grossRentMonthly));
        updateElement('grossRentAnnual', formatCurrency(grossRentAnnual));
        updateElement('effectiveIncomeMonthly', formatCurrency(effectiveIncomeMonthly));
        updateElement('totalExpensesMonthly', formatCurrency(totalExpensesMonthly));
        updateElement('noiMonthly', formatCurrency(noiMonthly));
        updateElement('downPaymentAmount', formatCurrency(downPayment));
        updateElement('loanAmount', formatCurrency(loanAmount));
        updateElement('monthlyPayment', formatCurrency(monthlyPayment));
        updateElement('cashDownPayment', formatCurrency(downPayment));
        updateElement('cashClosingCosts', formatCurrency(closingCosts));
        updateElement('cashRehabCosts', formatCurrency(rehabCosts));
        updateElement('totalCashNeeded', formatCurrency(totalCashNeeded));

        // Summary metrics
        updateElement('capRate', formatPercent(capRate));
        updateElement('cashOnCash', formatPercent(cashOnCash));
        updateElement('dscr', dscr.toFixed(2));
        updateElement('onePercentRule', formatPercent(onePercentRule));
        updateElement('grm', grm.toFixed(2));
        updateElement('monthlyCashFlow', formatCurrency(monthlyCashFlow));
        updateElement('annualCashFlow', formatCurrency(annualCashFlow));

        // Status badges
        updateStatusBadge('capRateStatus', capRate >= 0.08 ? 'pass' : (capRate >= 0.06 ? 'review' : 'fail'),
                         capRate >= 0.08 ? 'Good' : (capRate >= 0.06 ? 'Average' : 'Low'));
        updateStatusBadge('cashOnCashStatus', cashOnCash >= 0.10 ? 'pass' : (cashOnCash >= 0.06 ? 'review' : 'fail'),
                         cashOnCash >= 0.10 ? 'Good' : (cashOnCash >= 0.06 ? 'Average' : 'Low'));
        updateStatusBadge('dscrStatus', dscr >= 1.25 ? 'pass' : (dscr >= 1.0 ? 'review' : 'fail'),
                         dscr >= 1.25 ? 'Strong' : (dscr >= 1.0 ? 'Marginal' : 'Weak'));
        updateStatusBadge('onePercentStatus', onePercentRule >= 0.01 ? 'pass' : 'fail',
                         onePercentRule >= 0.01 ? 'Pass' : 'Fail');
        updateStatusBadge('grmStatus', grm <= 12 ? 'pass' : 'fail',
                         grm <= 12 ? 'Good' : 'High');

        // Rules check
        updateRuleStatus('rule1Status', onePercentRule >= 0.01);
        updateRuleStatus('rule2Status', onePercentRule >= 0.02);
        updateRuleStatus('rule50Status', expenseRatio <= 0.50);
        updateRuleStatus('rule70Status', purchasePrice <= rule70Max);
        updateRuleStatus('cashFlowPositive', monthlyCashFlow > 0);

        // Deal verdict
        updateDealVerdict(capRate, cashOnCash, dscr, monthlyCashFlow);

        // Store calculations for PDF
        window.investmentData = {
            // User info
            userName: document.getElementById('userName')?.value || '',
            userEmail: document.getElementById('userEmail')?.value || '',
            userPhone: document.getElementById('userPhone')?.value || '',

            // Property details
            propertyAddress: document.getElementById('propertyAddress')?.value || '',
            propertyCity: document.getElementById('propertyCity')?.value || '',
            propertyState: document.getElementById('propertyState')?.value || 'FL',
            propertyZip: document.getElementById('propertyZip')?.value || '',
            propertyType: document.getElementById('propertyType')?.value || '',
            numUnits: numUnits,
            sqft: getNum('sqft'),
            yearBuilt: getNum('yearBuilt'),
            bedrooms: getNum('bedrooms'),
            bathrooms: getNum('bathrooms'),
            lotSize: getNum('lotSize'),

            // Purchase info
            askingPrice: getNum('askingPrice'),
            purchasePrice: purchasePrice,
            arv: arv,
            rehabCosts: rehabCosts,
            closingCosts: closingCosts,

            // Income
            grossRentMonthly: grossRentMonthly,
            grossRentAnnual: grossRentAnnual,
            vacancyRate: vacancyRate,
            creditLoss: creditLoss,
            otherIncomeMonthly: otherIncomeMonthly,
            effectiveIncomeMonthly: effectiveIncomeMonthly,
            effectiveIncomeAnnual: effectiveIncomeAnnual,

            // Expenses
            propertyTaxes: propertyTaxes,
            insurance: insurance,
            propertyMgmt: propertyMgmt,
            repairs: repairs,
            capex: capex,
            utilities: utilities,
            waterSewer: waterSewer,
            trash: trash,
            lawnCare: lawnCare,
            hoaFees: hoaFees,
            pestControl: pestControl,
            otherExpenses: otherExpenses,
            totalExpensesMonthly: totalExpensesMonthly,
            totalExpensesAnnual: totalExpensesAnnual,

            // NOI
            noiMonthly: noiMonthly,
            noiAnnual: noiAnnual,

            // Financing
            downPaymentPercent: downPaymentPercent,
            interestRate: interestRate,
            loanTermYears: loanTermYears,
            downPayment: downPayment,
            loanAmount: loanAmount,
            monthlyPayment: monthlyPayment,
            annualDebtService: annualDebtService,
            totalCashNeeded: totalCashNeeded,

            // Cash flow
            monthlyCashFlow: monthlyCashFlow,
            annualCashFlow: annualCashFlow,

            // Metrics
            capRate: capRate,
            cashOnCash: cashOnCash,
            dscr: dscr,
            grm: grm,
            onePercentRule: onePercentRule,
            expenseRatio: expenseRatio,

            // Rules
            rule1Pass: onePercentRule >= 0.01,
            rule2Pass: onePercentRule >= 0.02,
            rule50Pass: expenseRatio <= 0.50,
            rule70Pass: purchasePrice <= rule70Max,
            cashFlowPositivePass: monthlyCashFlow > 0
        };
    }

    // Update element text
    function updateElement(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    // Update status badge
    function updateStatusBadge(id, status, text) {
        const el = document.getElementById(id);
        if (el) {
            el.className = 'status-badge ' + status;
            el.textContent = text;
        }
    }

    // Update rule status
    function updateRuleStatus(id, passed) {
        const el = document.getElementById(id);
        if (el) {
            el.className = 'rule-status ' + (passed ? 'pass' : 'fail');
            el.textContent = passed ? 'PASS' : 'FAIL';
        }
    }

    // Update deal verdict
    function updateDealVerdict(capRate, cashOnCash, dscr, monthlyCashFlow) {
        const verdictEl = document.getElementById('dealVerdict');
        if (!verdictEl) return;

        let score = 0;
        if (capRate >= 0.08) score += 2;
        else if (capRate >= 0.06) score += 1;

        if (cashOnCash >= 0.10) score += 2;
        else if (cashOnCash >= 0.06) score += 1;

        if (dscr >= 1.25) score += 2;
        else if (dscr >= 1.0) score += 1;

        if (monthlyCashFlow >= 200) score += 2;
        else if (monthlyCashFlow > 0) score += 1;

        let verdict, className;
        if (score >= 7) {
            verdict = 'STRONG BUY';
            className = 'strong-buy';
        } else if (score >= 5) {
            verdict = 'CONSIDER';
            className = 'consider';
        } else if (score >= 3) {
            verdict = 'REVIEW';
            className = 'review';
        } else {
            verdict = 'PASS';
            className = 'pass';
        }

        verdictEl.textContent = verdict;
        verdictEl.className = 'verdict ' + className;

        // Store verdict
        if (window.investmentData) {
            window.investmentData.verdict = verdict;
        }
    }

    // Update summary display
    function updateSummary() {
        const summaryProperty = document.getElementById('summaryProperty');
        if (summaryProperty && window.investmentData) {
            const data = window.investmentData;
            summaryProperty.innerHTML = `
                <p><strong>${data.propertyAddress}</strong></p>
                <p>${data.propertyCity}, ${data.propertyState} ${data.propertyZip}</p>
                <p>${data.propertyType} | ${data.bedrooms} Bed | ${data.bathrooms} Bath | ${data.sqft?.toLocaleString()} SF</p>
                <p>Purchase: ${formatCurrency(data.purchasePrice)}</p>
            `;
        }
    }

    // Handle form submission
    async function handleSubmit(e) {
        e.preventDefault();

        // Validate all required fields
        if (!validateStep(1) || !validateStep(2) || !validateStep(3)) {
            return;
        }

        // Show loading
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.add('active');
        submitBtn.disabled = true;

        try {
            // Make sure we have the latest calculations
            calculateAll();

            // Send data to server
            const response = await fetch('/api/generate-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(window.investmentData)
            });

            const result = await response.json();

            if (result.success) {
                // Show success modal
                document.getElementById('sentEmail').textContent = window.investmentData.userEmail;
                document.getElementById('successModal').classList.add('active');
            } else {
                alert('There was an error generating your report. Please try again.');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('There was an error sending your report. Please try again.');
        } finally {
            loadingOverlay.classList.remove('active');
            submitBtn.disabled = false;
        }
    }
});

// Close modal function
function closeModal() {
    document.getElementById('successModal').classList.remove('active');
}

// Close modal on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// Close modal on background click
document.getElementById('successModal')?.addEventListener('click', function(e) {
    if (e.target === this) {
        closeModal();
    }
});
