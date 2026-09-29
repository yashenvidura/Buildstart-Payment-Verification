import { useEffect, useState } from "react";


const API_BASE = "http://127.0.0.1:8000";


function StatusBadge({ value }) {
  if (!value) {
    return (
      <span className="badge neutral">
        N/A
      </span>
    );
  }

  const successValues = [
    "MATCH",
    "SUCCESS",
    "VALID",
    "PRESENT",
    "NEW",
    "OK",
  ];

  const dangerValues = [
    "MISMATCH",
    "FAILED",
    "DUPLICATE",
    "REUSED",
    "OLD",
    "CONFLICT",
  ];

  const warningValues = [
    "MISSING",
    "UNKNOWN",
    "PENDING",
    "SIMILAR",
    "DIFFERENT",
    "PARTIAL",
    "INSUFFICIENT",
    "NO_SMS",
    "OUTSIDE_WINDOW",
    "SUSPICIOUS",
  ];

  let type = "neutral";

  if (successValues.includes(value)) {
    type = "success";
  } else if (dangerValues.includes(value)) {
    type = "danger";
  } else if (warningValues.includes(value)) {
    type = "warning";
  }

  // NOT_STATED intentionally stays neutral.

  return (
    <span className={`badge ${type}`}>
      {value}
    </span>
  );
}


function InfoRow({ label, value }) {
  return (
    <div className="info-row">
      <span>{label}</span>

      <strong>
        {value || "Not detected"}
      </strong>
    </div>
  );
}


function CheckRow({ label, value }) {
  return (
    <div className="check-row">
      <span>{label}</span>

      <StatusBadge value={value} />
    </div>
  );
}


function App() {
  // --------------------------------------------------
  // PAYMENT VERIFICATION STATE
  // --------------------------------------------------

  const [orderId, setOrderId] = useState("1");

  const [receipt, setReceipt] = useState(null);

  const [
    receiptPreview,
    setReceiptPreview
  ] = useState(null);

  const [smsText, setSmsText] = useState("");

  const [result, setResult] = useState(null);

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState("");


  // --------------------------------------------------
  // ORDER MANAGEMENT STATE
  // --------------------------------------------------

  const [orders, setOrders] = useState([]);

  const [
    ordersLoading,
    setOrdersLoading
  ] = useState(false);

  const [
    showOrders,
    setShowOrders
  ] = useState(false);

  const [
    showNewOrder,
    setShowNewOrder
  ] = useState(false);

  const [
    creatingOrder,
    setCreatingOrder
  ] = useState(false);

  const [
    orderMessage,
    setOrderMessage
  ] = useState("");

  const [
    newOrder,
    setNewOrder
  ] = useState({
    customer_name: "",
    expected_amount: "",
    expected_account: "",
  });


  // --------------------------------------------------
  // CLEAN RECEIPT PREVIEW URL
  // --------------------------------------------------

  useEffect(() => {
    return () => {
      if (receiptPreview) {
        URL.revokeObjectURL(
          receiptPreview
        );
      }
    };
  }, [receiptPreview]);


  // --------------------------------------------------
  // RECEIPT FILE CHANGE
  // --------------------------------------------------

  function handleReceiptChange(event) {
    const file =
      event.target.files[0];

    if (receiptPreview) {
      URL.revokeObjectURL(
        receiptPreview
      );
    }

    if (!file) {
      setReceipt(null);
      setReceiptPreview(null);
      return;
    }

    setReceipt(file);

    setReceiptPreview(
      URL.createObjectURL(file)
    );
  }


  // --------------------------------------------------
  // LOAD ORDERS
  // --------------------------------------------------

  async function loadOrders(
    openModal = true
  ) {
    setOrdersLoading(true);

    try {
      const response = await fetch(
        `${API_BASE}/orders`
      );

      if (!response.ok) {
        throw new Error(
          "Could not load orders."
        );
      }

      const data =
        await response.json();

      setOrders(data);

      if (openModal) {
        setShowOrders(true);
      }

    } catch (err) {
      setError(
        err.message ||
        "Could not load orders."
      );

    } finally {
      setOrdersLoading(false);
    }
  }


  // --------------------------------------------------
  // CREATE NEW ORDER
  // --------------------------------------------------

  async function handleCreateOrder(
    event
  ) {
    event.preventDefault();

    setOrderMessage("");

    const customerName =
      newOrder.customer_name.trim();

    const account =
      newOrder.expected_account.trim();

    const amount = Number(
      newOrder.expected_amount
    );


    if (!customerName) {
      setOrderMessage(
        "Please enter the customer name."
      );

      return;
    }


    if (
      !Number.isFinite(amount) ||
      amount <= 0
    ) {
      setOrderMessage(
        "Please enter a valid expected amount."
      );

      return;
    }


    if (!account) {
      setOrderMessage(
        "Please enter the receiving account."
      );

      return;
    }


    setCreatingOrder(true);


    try {
      const response = await fetch(
        `${API_BASE}/orders`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            customer_name:
              customerName,

            expected_amount:
              amount,

            expected_account:
              account,
          }),
        }
      );


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
          "Could not create order."
        );
      }


      // Automatically select the
      // newly created order.
      setOrderId(
        String(data.id)
      );


      // Clear any previous verification
      // result because we are now working
      // with another order.
      setResult(null);

      setError("");


      // Reset new-order form.
      setNewOrder({
        customer_name: "",
        expected_amount: "",
        expected_account: "",
      });


      setShowNewOrder(false);


      // Refresh order list in memory.
      await loadOrders(false);

    } catch (err) {
      setOrderMessage(
        err.message ||
        "Could not create order."
      );

    } finally {
      setCreatingOrder(false);
    }
  }


  // --------------------------------------------------
  // VERIFY PAYMENT
  // --------------------------------------------------

  async function handleSubmit(event) {
    event.preventDefault();

    if (!receipt) {
      setError(
        "Please select a payment receipt."
      );

      return;
    }


    setLoading(true);
    setError("");
    setResult(null);


    const formData =
      new FormData();


    formData.append(
      "order_id",
      orderId
    );


    formData.append(
      "receipt",
      receipt
    );


    if (smsText.trim()) {
      formData.append(
        "sms_text",
        smsText.trim()
      );
    }


    try {
      const response = await fetch(
        `${API_BASE}/payments/verify`,
        {
          method: "POST",
          body: formData,
        }
      );


      const data =
        await response.json();


      if (!response.ok) {
        throw new Error(
          data.detail ||
          "Payment verification failed."
        );
      }


      setResult(data);

    } catch (err) {
      setError(
        err.message ||
        "Could not connect to the verification server."
      );

    } finally {
      setLoading(false);
    }
  }


  // --------------------------------------------------
  // DECISION STYLE
  // --------------------------------------------------

  function getDecisionClass(
    decision
  ) {
    if (decision === "APPROVED") {
      return "approved";
    }

    if (decision === "REJECTED") {
      return "rejected";
    }

    return "needs-verification";
  }


  // --------------------------------------------------
  // RESULT DATA
  // --------------------------------------------------

  const extracted =
    result?.extracted_fields || {};

  const verification =
    result?.verification || {};

  const fraud =
    result?.fraud || {};

  const sms =
    result?.sms || {
      status: "NO_SMS",
      checks: {},
    };

  const quality =
    result?.image_quality || {};


  const extractedAmount =
    extracted.amount_candidates?.[0];


  const detectedAccounts =
    extracted.account_candidates?.length
      ? extracted.account_candidates.join(
          ", "
        )
      : null;


  return (
    <div className="app-shell">

      {/* ==========================================
          CREATE NEW ORDER MODAL
      =========================================== */}

      {showNewOrder && (
        <div className="orders-overlay">

          <div className="new-order-modal">

            <div className="orders-modal-header">

              <div>
                <span className="eyebrow">
                  ORDER MANAGEMENT
                </span>

                <h2>
                  Create New Order
                </h2>

                <p>
                  Enter the expected payment
                  information before the customer
                  submits a receipt.
                </p>
              </div>


              <button
                type="button"
                className="close-orders-button"
                aria-label="Close new order form"
                onClick={() =>
                  setShowNewOrder(false)
                }
              >
                ×
              </button>

            </div>


            <form
              className="new-order-form"
              onSubmit={
                handleCreateOrder
              }
            >

              <label>
                Customer Name

                <input
                  type="text"
                  value={
                    newOrder.customer_name
                  }
                  placeholder="e.g. John Silva"
                  required
                  onChange={(event) =>
                    setNewOrder({
                      ...newOrder,

                      customer_name:
                        event.target.value,
                    })
                  }
                />
              </label>


              <label>
                Expected Amount

                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={
                    newOrder.expected_amount
                  }
                  placeholder="e.g. 4000.00"
                  required
                  onChange={(event) =>
                    setNewOrder({
                      ...newOrder,

                      expected_amount:
                        event.target.value,
                    })
                  }
                />
              </label>


              <label>
                Receiving Account

                <input
                  type="text"
                  value={
                    newOrder.expected_account
                  }
                  placeholder="Business bank account"
                  required
                  onChange={(event) =>
                    setNewOrder({
                      ...newOrder,

                      expected_account:
                        event.target.value,
                    })
                  }
                />
              </label>


              {orderMessage && (
                <div className="order-form-error">
                  {orderMessage}
                </div>
              )}


              <div className="new-order-actions">

                <button
                  type="button"
                  className="cancel-order-button"
                  onClick={() =>
                    setShowNewOrder(false)
                  }
                >
                  Cancel
                </button>


                <button
                  type="submit"
                  className="create-order-button"
                  disabled={creatingOrder}
                >
                  {creatingOrder
                    ? "Creating..."
                    : "Create Order"}
                </button>

              </div>

            </form>

          </div>

        </div>
      )}


      {/* ==========================================
          ORDERS TABLE MODAL
      =========================================== */}

      {showOrders && (
        <div className="orders-overlay">

          <div className="orders-modal">

            <div className="orders-modal-header">

              <div>
                <span className="eyebrow">
                  BUSINESS ORDERS
                </span>

                <h2>
                  Recorded Orders
                </h2>

                <p>
                  Select an order to use it
                  for payment verification.
                </p>
              </div>


              <button
                type="button"
                className="close-orders-button"
                aria-label="Close orders"
                onClick={() =>
                  setShowOrders(false)
                }
              >
                ×
              </button>

            </div>


            {orders.length === 0 ? (

              <div className="orders-empty">
                No orders have been recorded.
              </div>

            ) : (

              <div className="orders-table-wrapper">

                <table className="orders-table">

                  <thead>
                    <tr>
                      <th>Order</th>
                      <th>Customer</th>
                      <th>Expected Amount</th>
                      <th>Expected Account</th>
                      <th>Created</th>
                      <th></th>
                    </tr>
                  </thead>


                  <tbody>

                    {orders.map(
                      (order) => (

                        <tr
                          key={order.id}
                          className={
                            String(order.id) ===
                            String(orderId)
                              ? "active-order-row"
                              : ""
                          }
                        >

                          <td>
                            <strong>
                              #{order.id}
                            </strong>
                          </td>


                          <td>
                            {
                              order.customer_name
                            }
                          </td>


                          <td
                            className="amount-cell"
                          >
                            {Number(
                              order.expected_amount
                            ).toLocaleString(
                              undefined,
                              {
                                minimumFractionDigits:
                                  2,

                                maximumFractionDigits:
                                  2,
                              }
                            )}
                          </td>


                          <td
                            className="account-cell"
                          >
                            {
                              order.expected_account
                            }
                          </td>


                          <td>
                            {new Date(
                              order.created_at
                            ).toLocaleString()}
                          </td>


                          <td>

                            <button
                              type="button"
                              className="select-order-button"
                              onClick={() => {

                                setOrderId(
                                  String(
                                    order.id
                                  )
                                );

                                setResult(null);

                                setShowOrders(
                                  false
                                );
                              }}
                            >
                              Select
                            </button>

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

          </div>

        </div>
      )}


      {/* ==========================================
          LOADING OVERLAY
      =========================================== */}

      {loading && (
        <div className="loading-overlay">

          <div className="loading-card">

            <div className="spinner"></div>

            <h2>
              Verifying payment
            </h2>

            <p>
              Checking receipt details,
              payment history, duplicates
              and available bank evidence.
            </p>

            <div className="loading-steps">
              <span>OCR</span>
              <span>Verification</span>
              <span>Fraud checks</span>
            </div>

          </div>

        </div>
      )}


      {/* ==========================================
          HEADER
      =========================================== */}

      <header className="topbar">

        <div className="brand-area">

          <div className="brand-icon">
            ✓
          </div>

          <div>
            <h1>
              Payment Verification
            </h1>

            <p>
              Automated bank-transfer
              verification dashboard
            </p>
          </div>

        </div>


        <div className="topbar-actions">

          <button
            type="button"
            className="new-order-button"
            onClick={() => {
              setOrderMessage("");
              setShowNewOrder(true);
            }}
          >
            + New Order
          </button>


          <button
            type="button"
            className="orders-button"
            onClick={() =>
              loadOrders(true)
            }
            disabled={ordersLoading}
          >
            {ordersLoading
              ? "Loading..."
              : "View Orders"}
          </button>


          <div className="system-online">

            <span className="online-dot">
            </span>

            System online

          </div>

        </div>

      </header>


      {/* ==========================================
          MAIN CONTENT
      =========================================== */}

      <main className="dashboard">


        {/* ========================================
            LEFT PANEL
        ========================================= */}

        <section className="card input-card">

          <div className="section-heading">

            <div>
              <span className="eyebrow">
                PAYMENT EVIDENCE
              </span>

              <h2>
                New Verification
              </h2>
            </div>

            <p>
              Submit the customer's receipt
              and optional bank SMS evidence.
            </p>

          </div>


          <form onSubmit={handleSubmit}>

            <div className="form-group">

              <label htmlFor="orderId">
                Order ID
              </label>

              <input
                id="orderId"
                type="number"
                min="1"
                required
                value={orderId}
                onChange={(event) =>
                  setOrderId(
                    event.target.value
                  )
                }
              />

            </div>


            <div className="form-group">

              <label htmlFor="receipt">
                Payment Receipt
              </label>

              <input
                id="receipt"
                type="file"
                accept="image/*"
                required
                onChange={
                  handleReceiptChange
                }
              />

              <span className="helper-text">
                Upload a screenshot or
                photograph of the bank receipt.
              </span>

            </div>


            {receiptPreview && (
              <div className="receipt-preview">

                <div className="preview-header">

                  <span>
                    Receipt preview
                  </span>

                  <span className="file-name">
                    {receipt?.name}
                  </span>

                </div>

                <img
                  src={receiptPreview}
                  alt="Uploaded payment receipt"
                />

              </div>
            )}


            <div className="form-group">

              <div className="label-row">

                <label htmlFor="sms">
                  Bank SMS
                </label>

                <span className="optional-tag">
                  Optional
                </span>

              </div>

              <textarea
                id="sms"
                rows="6"
                value={smsText}
                placeholder="Paste the bank SMS notification here..."
                onChange={(event) =>
                  setSmsText(
                    event.target.value
                  )
                }
              />

              <span className="helper-text">
                Missing SMS does not
                automatically reject a payment.
              </span>

            </div>


            <button
              className="verify-button"
              type="submit"
              disabled={loading}
            >

              <span>
                {loading
                  ? "Verifying..."
                  : "Verify Payment"}
              </span>

              {!loading && (
                <span className="button-arrow">
                  →
                </span>
              )}

            </button>

          </form>


          {error && (
            <div className="error-message">

              <strong>
                Verification error
              </strong>

              <span>
                {error}
              </span>

            </div>
          )}

        </section>


        {/* ========================================
            RIGHT PANEL
        ========================================= */}

        <section className="card result-card">

          {!result && (
            <div className="empty-state">

              <div className="empty-icon">
                ✓
              </div>

              <h2>
                Ready to verify
              </h2>

              <p>
                Upload payment evidence and
                click Verify Payment to see
                the system's conclusion.
              </p>

              <div className="empty-features">

                <span>
                  ✓ Receipt verification
                </span>

                <span>
                  ✓ Duplicate detection
                </span>

                <span>
                  ✓ SMS evidence
                </span>

              </div>

            </div>
          )}


          {result && (
            <div
              key={
                result.payment_submission_id
              }
              className="result-content"
            >

              {/* FINAL DECISION */}

              <div
                className={
                  `decision-card ${
                    getDecisionClass(
                      result.decision
                    )
                  }`
                }
              >

                <div className="decision-top">

                  <span className="decision-title">
                    FINAL DECISION
                  </span>

                  <span className="submission-id">
                    Submission #
                    {
                      result.payment_submission_id
                    }
                  </span>

                </div>

                <h2>
                  {result.decision}
                </h2>

                <p>
                  {result.reason}
                </p>

              </div>


              {/* NEXT ACTION */}

              <div className="next-action-card">

                <div className="next-action-icon">
                  →
                </div>

                <div>

                  <span>
                    RECOMMENDED NEXT ACTION
                  </span>

                  <p>
                    {result.next_action}
                  </p>

                </div>

              </div>


              {/* EXTRACTED INFORMATION */}

              <div className="result-section">

                <div className="section-title-row">

                  <div>
                    <span className="eyebrow">
                      CUSTOMER EVIDENCE
                    </span>

                    <h3>
                      Extracted Payment Information
                    </h3>
                  </div>

                  <span className="section-tag">
                    OCR
                  </span>

                </div>


                <div className="info-grid">

                  <InfoRow
                    label="Amount"
                    value={
                      extractedAmount
                        ? `${
                            extracted.currency ||
                            ""
                          } ${extractedAmount}`
                        : null
                    }
                  />

                  <InfoRow
                    label="Receipt reference"
                    value={
                      extracted.receipt_reference
                    }
                  />

                  <InfoRow
                    label="Transaction time"
                    value={
                      extracted.transaction_datetime
                    }
                  />

                  <InfoRow
                    label="Receipt status"
                    value={
                      extracted.status
                    }
                  />

                  <InfoRow
                    label="Currency"
                    value={
                      extracted.currency
                    }
                  />

                  <InfoRow
                    label="Detected accounts"
                    value={
                      detectedAccounts
                    }
                  />

                </div>

              </div>


              {/* VERIFICATION */}

              <div className="result-section">

                <div className="section-title-row">

                  <div>
                    <span className="eyebrow">
                      SYSTEM CONCLUSION
                    </span>

                    <h3>
                      Verification Checks
                    </h3>
                  </div>

                </div>


                <div className="checks-container">

                  <CheckRow
                    label="Payment amount"
                    value={
                      verification.amount_check
                    }
                  />

                  <CheckRow
                    label="Beneficiary account"
                    value={
                      verification.account_check
                    }
                  />

                  <CheckRow
                    label="Transaction status"
                    value={
                      verification.status_check
                    }
                  />

                  <CheckRow
                    label="Receipt reference"
                    value={
                      verification.reference_check
                    }
                  />

                  <CheckRow
                    label="Transaction date"
                    value={
                      verification.date_check
                    }
                  />

                </div>

              </div>


              {/* FRAUD */}

              <div className="result-section">

                <div className="section-title-row">

                  <div>
                    <span className="eyebrow">
                      RISK ANALYSIS
                    </span>

                    <h3>
                      Fraud & Duplicate Checks
                    </h3>
                  </div>

                </div>


                <div className="checks-container">

                  <CheckRow
                    label="Receipt reference reuse"
                    value={
                      fraud.reference_reuse
                    }
                  />

                  <CheckRow
                    label="Exact image duplicate"
                    value={
                      fraud.exact_duplicate
                    }
                  />

                  <CheckRow
                    label="Similar receipt image"
                    value={
                      fraud.similar_image
                        ?.status
                    }
                  />

                </div>


                {fraud.similar_image
                  ?.distance !== null &&
                  fraud.similar_image
                    ?.distance !==
                    undefined && (

                    <div className="technical-note">

                      Perceptual image distance:

                      <strong>
                        {" "}
                        {
                          fraud.similar_image
                            .distance
                        }
                      </strong>

                    </div>
                  )}

              </div>


              {/* SMS */}

              <div className="result-section">

                <div className="section-title-row">

                  <div>
                    <span className="eyebrow">
                      SUPPORTING EVIDENCE
                    </span>

                    <h3>
                      Bank SMS Evidence
                    </h3>
                  </div>

                  <StatusBadge
                    value={
                      sms.status ||
                      "NO_SMS"
                    }
                  />

                </div>


                {sms.checks &&
                Object.keys(
                  sms.checks
                ).length > 0 ? (

                  <div className="checks-container">

                    {Object.entries(
                      sms.checks
                    ).map(
                      ([key, value]) => (

                        <CheckRow
                          key={key}
                          label={
                            key
                              .replace(
                                /_/g,
                                " "
                              )
                              .replace(
                                /^\w/,
                                (letter) =>
                                  letter
                                    .toUpperCase()
                              )
                          }
                          value={value}
                        />

                      )
                    )}

                  </div>

                ) : (

                  <div className="no-evidence">

                    No bank SMS was supplied
                    for this verification.

                  </div>

                )}

              </div>


              {/* IMAGE QUALITY */}

              <div className="result-section">

                <div className="section-title-row">

                  <div>
                    <span className="eyebrow">
                      RECEIPT QUALITY
                    </span>

                    <h3>
                      Image Analysis
                    </h3>
                  </div>

                </div>


                <div className="checks-container">

                  <CheckRow
                    label="Resolution"
                    value={
                      quality.resolution_check
                    }
                  />

                  <CheckRow
                    label="Blur detection"
                    value={
                      quality.blur_check
                    }
                  />

                  <CheckRow
                    label="Brightness"
                    value={
                      quality.brightness_check
                    }
                  />

                  <CheckRow
                    label="Editing metadata"
                    value={
                      quality.metadata_suspicious
                        ? "SUSPICIOUS"
                        : "OK"
                    }
                  />

                </div>


                <div className="quality-metrics">

                  <span>
                    {quality.width || "?"}
                    ×
                    {quality.height || "?"}
                    {" "}px
                  </span>


                  {quality.blur_score !==
                    undefined && (

                    <span>
                      Blur score:{" "}
                      {quality.blur_score}
                    </span>

                  )}


                  {quality.contrast !==
                    undefined && (

                    <span>
                      Contrast:{" "}
                      {quality.contrast}
                    </span>

                  )}

                </div>

              </div>

            </div>
          )}

        </section>

      </main>


      <footer className="footer">

        Automated Payment Verification
        Prototype

      </footer>

    </div>
  );
}


export default App;