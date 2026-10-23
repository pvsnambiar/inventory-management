<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click="close">
        <div class="modal-container" @click.stop>
          <div class="modal-header">
            <h3 class="modal-title">{{ mode === 'create' ? 'Create Purchase Order' : 'View Purchase Order' }}</h3>
            <button class="close-button" @click="close">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <div class="modal-body" v-if="backlogItem">
            <div class="po-header">
              <div class="header-section">
                <div class="header-label">Item</div>
                <div class="header-value">{{ backlogItem.item_name }}</div>
              </div>
              <div class="header-section">
                <div class="header-label">SKU</div>
                <div class="header-value sku">{{ backlogItem.item_sku }}</div>
              </div>
              <div class="header-section">
                <div class="header-label">Quantity Needed</div>
                <div class="header-value">{{ backlogItem.quantity_needed }} units</div>
              </div>
            </div>

            <div v-if="mode === 'create'" class="form-section">
              <div class="form-group">
                <label class="form-label">Supplier</label>
                <input
                  v-model="formData.supplier"
                  type="text"
                  class="form-input"
                  placeholder="Enter supplier name"
                />
              </div>

              <div class="form-group">
                <label class="form-label">Quantity to Order</label>
                <input
                  v-model.number="formData.quantity"
                  type="number"
                  class="form-input"
                  :max="backlogItem.quantity_needed * 2"
                  :min="backlogItem.quantity_needed"
                />
              </div>

              <div class="form-group">
                <label class="form-label">Unit Price</label>
                <input
                  v-model.number="formData.unitPrice"
                  type="number"
                  class="form-input"
                  step="0.01"
                  min="0"
                />
              </div>

              <div class="form-group">
                <label class="form-label">Expected Delivery Date</label>
                <input
                  v-model="formData.deliveryDate"
                  type="date"
                  class="form-input"
                />
              </div>

              <div class="summary-section">
                <div class="summary-item">
                  <span class="summary-label">Total Cost:</span>
                  <span class="summary-value">${{ (formData.quantity * formData.unitPrice).toFixed(2) }}</span>
                </div>
              </div>
            </div>

            <div v-else class="view-section">
              <div class="info-grid">
                <div class="info-item">
                  <div class="info-label">PO ID</div>
                  <div class="info-value">{{ backlogItem.purchase_order?.id || 'N/A' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Supplier</div>
                  <div class="info-value">{{ backlogItem.purchase_order?.supplier || 'N/A' }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Order Quantity</div>
                  <div class="info-value">{{ backlogItem.purchase_order?.quantity || 'N/A' }} units</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Unit Price</div>
                  <div class="info-value">${{ (backlogItem.purchase_order?.unit_price || 0).toFixed(2) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Total Cost</div>
                  <div class="info-value"><strong>${{ ((backlogItem.purchase_order?.quantity || 0) * (backlogItem.purchase_order?.unit_price || 0)).toFixed(2) }}</strong></div>
                </div>
                <div class="info-item">
                  <div class="info-label">Expected Delivery</div>
                  <div class="info-value">{{ formatDate(backlogItem.purchase_order?.expected_delivery) }}</div>
                </div>
                <div class="info-item">
                  <div class="info-label">Status</div>
                  <div class="info-value">
                    <span :class="['badge', getStatusClass(backlogItem.purchase_order?.status)]">
                      {{ backlogItem.purchase_order?.status || 'Unknown' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-secondary" @click="close">{{ mode === 'create' ? 'Cancel' : 'Close' }}</button>
            <button v-if="mode === 'create'" class="btn-primary" @click="submitPO" :disabled="isSubmitting">
              {{ isSubmitting ? 'Creating...' : 'Create PO' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api } from '../api'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  },
  mode: {
    type: String,
    enum: ['create', 'view'],
    default: 'create'
  }
})

const emit = defineEmits(['close', 'po-created'])

const isSubmitting = ref(false)
const formData = reactive({
  supplier: '',
  quantity: props.backlogItem?.quantity_needed || 0,
  unitPrice: 0,
  deliveryDate: ''
})

const close = () => {
  resetForm()
  emit('close')
}

const resetForm = () => {
  formData.supplier = ''
  formData.quantity = props.backlogItem?.quantity_needed || 0
  formData.unitPrice = 0
  formData.deliveryDate = ''
}

const submitPO = async () => {
  if (!formData.supplier || !formData.quantity || !formData.unitPrice) {
    alert('Please fill in all required fields')
    return
  }

  isSubmitting.value = true
  try {
    const poData = {
      backlog_item_id: props.backlogItem.id,
      supplier: formData.supplier,
      quantity: formData.quantity,
      unit_price: formData.unitPrice,
      expected_delivery: formData.deliveryDate,
      item_sku: props.backlogItem.item_sku,
      item_name: props.backlogItem.item_name
    }

    const response = await api.createPurchaseOrder(poData)
    emit('po-created', response)
    resetForm()
  } catch (error) {
    console.error('Failed to create purchase order:', error)
    alert('Failed to create purchase order: ' + error.message)
  } finally {
    isSubmitting.value = false
  }
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const getStatusClass = (status) => {
  const statusMap = {
    'pending': 'warning',
    'ordered': 'info',
    'received': 'success',
    'cancelled': 'danger'
  }
  return statusMap[status?.toLowerCase()] || 'secondary'
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.modal-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.025em;
}

.close-button {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.close-button:hover {
  background: #f1f5f9;
  color: #0f172a;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
}

.po-header {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 1.5rem;
}

.header-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.header-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.header-value {
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
}

.header-value.sku {
  font-family: 'Monaco', 'Courier New', monospace;
  color: #2563eb;
  font-size: 0.875rem;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
}

.form-input {
  padding: 0.625rem 0.875rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.875rem;
  font-family: inherit;
  transition: border-color 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.summary-section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 1rem;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #64748b;
}

.summary-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
}

.view-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-label {
  font-size: 0.813rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.info-value {
  font-size: 0.938rem;
  color: #0f172a;
  font-weight: 500;
}

.badge {
  display: inline-block;
  padding: 0.375rem 0.75rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
  width: fit-content;
}

.badge.success {
  background: #d1fae5;
  color: #065f46;
}

.badge.warning {
  background: #fef3c7;
  color: #92400e;
}

.badge.danger {
  background: #fee2e2;
  color: #991b1b;
}

.badge.info {
  background: #dbeafe;
  color: #1e40af;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.btn-primary {
  padding: 0.625rem 1.5rem;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 0.625rem 1.25rem;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-weight: 500;
  font-size: 0.875rem;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn-secondary:hover {
  background: #e2e8f0;
  border-color: #cbd5e1;
}

/* Modal transition animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.2s ease;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: scale(0.95);
}
</style>
