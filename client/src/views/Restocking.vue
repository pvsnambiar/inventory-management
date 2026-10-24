<template>
  <div class="restocking">
    <div class="page-header">
      <h2>Restocking</h2>
      <p>Get budget-based restocking recommendations and place a restocking order.</p>
    </div>

    <div v-if="orderResult" class="success-message">
      <span>
        Order <strong>{{ orderResult.order_number }}</strong> placed successfully.
      </span>
      <router-link to="/orders" class="view-orders-link">View in Orders</router-link>
      <button class="btn btn-secondary" @click="reset">Start New Restock</button>
    </div>

    <template v-else>
      <div class="card budget-card">
        <div class="card-header">
          <h3 class="card-title">Budget</h3>
          <span class="budget-value">{{ formatCurrency(budget) }}</span>
        </div>
        <div class="budget-controls">
          <input
            v-model.number="budget"
            type="range"
            min="0"
            max="100000"
            step="1000"
            class="budget-slider"
            aria-label="Restocking budget"
            :disabled="loading || placing"
          />
          <div class="slider-labels">
            <span>{{ formatCurrency(0) }}</span>
            <span>{{ formatCurrency(100000) }}</span>
          </div>
          <div class="actions">
            <button class="btn btn-primary" :disabled="loading || placing" @click="getRecommendations">
              {{ loading ? 'Loading...' : 'Get Recommendations' }}
            </button>
            <button class="btn btn-secondary" :disabled="loading || placing" @click="reset">Reset</button>
          </div>
        </div>
      </div>

      <div v-if="loading" class="loading">Loading recommendations...</div>
      <div v-else-if="error" class="error">{{ error }}</div>

      <template v-else-if="hasFetched">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">Recommended Items ({{ items.length }})</h3>
          </div>

          <div v-if="items.length === 0" class="empty">
            No items could be recommended for this budget.
          </div>
          <div v-else class="table-container">
            <table class="restock-table">
              <thead>
                <tr>
                  <th>SKU</th>
                  <th>Name</th>
                  <th>Category</th>
                  <th class="num">Demand Forecast</th>
                  <th class="num">Unit Cost</th>
                  <th class="num">Qty</th>
                  <th class="num">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in items" :key="item.sku">
                  <td><strong>{{ item.sku }}</strong></td>
                  <td>{{ item.name }}</td>
                  <td>{{ item.category }}</td>
                  <td class="num">{{ item.forecasted_demand }}</td>
                  <td class="num">{{ formatCurrency(item.unit_cost) }}</td>
                  <td class="num">{{ item.recommended_quantity }}</td>
                  <td class="num"><strong>{{ formatCurrency(item.item_total_cost) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="items.length > 0" class="card summary-bar">
          <div class="summary-item">
            <span class="summary-label">Total Cost</span>
            <span class="summary-value">{{ formatCurrency(summary.total_cost) }}</span>
          </div>
          <div class="summary-item">
            <span class="summary-label">Budget Used</span>
            <span class="summary-value">{{ summary.budget_used_percent.toFixed(1) }}%</span>
            <div class="progress">
              <div
                class="progress-fill"
                :class="{ over: summary.budget_used_percent > 100 }"
                :style="{ width: Math.min(summary.budget_used_percent, 100) + '%' }"
              ></div>
            </div>
          </div>
          <div class="summary-item">
            <span class="summary-label">Remaining</span>
            <span class="summary-value">{{ formatCurrency(summary.budget_remaining) }}</span>
          </div>
          <div class="summary-action">
            <div v-if="placeError" class="inline-error">{{ placeError }}</div>
            <button class="btn btn-primary" :disabled="placing" @click="placeOrder">
              {{ placing ? 'Placing...' : 'Place Order' }}
            </button>
          </div>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { api } from '../api'

const currencyFormatter = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export default {
  name: 'Restocking',
  setup() {
    const budget = ref(50000)
    const loading = ref(false)
    const placing = ref(false)
    const error = ref(null)
    const placeError = ref(null)
    const hasFetched = ref(false)
    const recommendation = ref(null)
    const orderResult = ref(null)

    const items = computed(() => recommendation.value?.recommended_items ?? [])
    const summary = computed(() => ({
      total_cost: recommendation.value?.total_cost ?? 0,
      budget_used_percent: recommendation.value?.budget_used_percent ?? 0,
      budget_remaining: recommendation.value?.budget_remaining ?? budget.value
    }))

    const formatCurrency = (value) => currencyFormatter.format(Number(value) || 0)

    const getRecommendations = async () => {
      try {
        loading.value = true
        error.value = null
        placeError.value = null
        recommendation.value = await api.getRestockingRecommendations({
          budget: budget.value,
          warehouse: 'all',
          category: 'all'
        })
        hasFetched.value = true
      } catch (err) {
        error.value = 'Failed to load recommendations: ' + err.message
        console.error('Recommendation error:', err)
      } finally {
        loading.value = false
      }
    }

    const placeOrder = async () => {
      if (items.value.length === 0) return
      try {
        placing.value = true
        placeError.value = null
        const orderItems = items.value.map(item => ({
          sku: item.sku,
          name: item.name,
          quantity: Math.floor(item.recommended_quantity),
          unit_price: item.unit_cost
        }))
        orderResult.value = await api.createRestockingOrder(orderItems)
      } catch (err) {
        placeError.value = 'Failed to place order: ' + err.message
        console.error('Place order error:', err)
      } finally {
        placing.value = false
      }
    }

    const reset = () => {
      budget.value = 50000
      recommendation.value = null
      hasFetched.value = false
      error.value = null
      placeError.value = null
      orderResult.value = null
    }

    return {
      budget,
      loading,
      placing,
      error,
      placeError,
      hasFetched,
      orderResult,
      items,
      summary,
      formatCurrency,
      getRecommendations,
      placeOrder,
      reset
    }
  }
}
</script>

<style scoped>
.budget-card,
.card + .card {
  margin-top: 1.5rem;
}

.budget-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--blue-600, #2563eb);
}

.budget-controls {
  padding: 0 1.5rem 1.5rem;
}

.budget-slider {
  width: 100%;
  accent-color: var(--blue-600, #2563eb);
}

.slider-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.813rem;
  color: #64748b;
}

.actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  border: 1px solid var(--border-color, #e2e8f0);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--blue-600, #2563eb);
  border-color: var(--blue-600, #2563eb);
  color: #fff;
}

.btn-secondary {
  background: var(--card-bg, #fff);
  color: var(--text-primary, #0f172a);
}

.restock-table {
  width: 100%;
  border-collapse: collapse;
}

.restock-table .num {
  text-align: right;
}

.empty {
  padding: 1.5rem;
  color: #64748b;
}

.summary-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr) auto;
  gap: 1.5rem;
  align-items: center;
  padding: 1.25rem 1.5rem;
  background: var(--card-bg, #fff);
  border: 1px solid var(--border-color, #e2e8f0);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.813rem;
  color: #64748b;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-primary, #0f172a);
}

.progress {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--green-500, #22c55e);
}

.progress-fill.over {
  background: var(--red-500, #ef4444);
}

.summary-action {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.inline-error {
  color: var(--red-500, #ef4444);
  font-size: 0.813rem;
}

.success-message {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.5rem;
  border: 1px solid var(--green-500, #22c55e);
  background: #f0fdf4;
  border-radius: 8px;
  color: var(--text-primary, #0f172a);
}

.view-orders-link {
  color: var(--blue-600, #2563eb);
  font-weight: 500;
  margin-left: auto;
}
</style>
