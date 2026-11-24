
import { useEffect, useState } from "react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiStatus, setApiStatus] = useState("Checking");

  async function loadDashboard() {
    try {
      const [doctorResponse, appointmentResponse] = await Promise.all([
        fetch(`${API}/api/doctors`),
        fetch(`${API}/api/appointments`),
      ]);

      if (!doctorResponse.ok || !appointmentResponse.ok) {
        throw new Error("API request failed");
      }

      const doctorData = await doctorResponse.json();
      const appointmentData = await appointmentResponse.json();

      setDoctors(Array.isArray(doctorData) ? doctorData : []);
      setAppointments(
        Array.isArray(appointmentData) ? appointmentData : []
      );
      setApiStatus("Connected");
    } catch {
      setApiStatus("Disconnected");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
    const interval = setInterval(loadDashboard, 5000);
    return () => clearInterval(interval);
  }, []);

  const getValue = (item, keys, fallback = "—") => {
    for (const key of keys) {
      if (item?.[key] !== undefined && item?.[key] !== null) {
        return item[key];
      }
    }
    return fallback;
  };

  return (
    <div className="dashboard">
      <header className="topbar">
        <div>
          <h1>CareVoice</h1>
          <p>AI Doctor Appointment Assistant</p>
        </div>
        <div className={`status ${apiStatus.toLowerCase()}`}>
          <span className="status-dot"></span>
          Backend: {apiStatus}
        </div>
      </header>

      <main>
        <section className="welcome">
          <div>
            <h2>Doctor Appointment Dashboard</h2>
            <p>Manage doctors, appointments and voice consultations.</p>
          </div>
          <button onClick={loadDashboard}>Refresh Data</button>
        </section>

        <section className="stats">
          <div className="stat-card">
            <span>Total Doctors</span>
            <strong>{doctors.length}</strong>
          </div>
          <div className="stat-card">
            <span>Total Appointments</span>
            <strong>{appointments.length}</strong>
          </div>
          <div className="stat-card">
            <span>Booked</span>
            <strong>
              {appointments.filter(
                (a) => String(a.status).toLowerCase() === "booked"
              ).length}
            </strong>
          </div>
          <div className="stat-card">
            <span>Cancelled</span>
            <strong>
              {appointments.filter(
                (a) => String(a.status).toLowerCase() === "cancelled"
              ).length}
            </strong>
          </div>
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <h2>Voice Assistant</h2>
              <p>Start a browser voice conversation with the assistant.</p>
            </div>
            <span className="live-label">VOICE CALL</span>
          </div>

          <iframe
            title="Voice AI Doctor Assistant"
            src="http://localhost:7860/client"
            className="voice-frame"
            allow="microphone; autoplay"
          />
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <h2>Available Doctors</h2>
              <p>Doctors registered in the appointment system.</p>
            </div>
          </div>

          {loading ? (
            <p className="empty">Loading doctors...</p>
          ) : doctors.length === 0 ? (
            <p className="empty">No doctors found or backend unavailable.</p>
          ) : (
            <div className="doctor-grid">
              {doctors.map((doctor, index) => (
                <div className="doctor-card" key={doctor.id ?? index}>
                  <div className="doctor-avatar">
                    {String(getValue(doctor, ["name"], "D"))
                      .charAt(0)
                      .toUpperCase()}
                  </div>
                  <h3>{getValue(doctor, ["name"])}</h3>
                  <p>{getValue(doctor, ["specialty"])}</p>
                  <div className="doctor-details">
                    <span>
                      Experience:{" "}
                      {getValue(doctor, ["experience", "experience_years"])}
                    </span>
                    <span>
                      Fee: ₹
                      {getValue(doctor, [
                        "consultation_fee",
                        "fee",
                      ])}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="panel">
          <div className="section-heading">
            <div>
              <h2>Appointment Updates</h2>
              <p>Latest appointments from the database.</p>
            </div>
          </div>

          {appointments.length === 0 ? (
            <p className="empty">No appointments available.</p>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Patient</th>
                    <th>Doctor</th>
                    <th>Specialty</th>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {appointments.map((appointment, index) => (
                    <tr key={appointment.id ?? index}>
                      <td>{getValue(appointment, ["appointment_id", "id"])}</td>
                      <td>{getValue(appointment, ["patient_name"], "Patient")}</td>
                      <td>{getValue(appointment, ["doctor_name"])}</td>
                      <td>{getValue(appointment, ["specialty"])}</td>
                      <td>
                        {getValue(appointment, [
                          "appointment_date",
                          "date",
                        ])}
                      </td>
                      <td>{getValue(appointment, ["slot_time", "time"])}</td>
                      <td>
                        <span
                          className={`appointment-status ${String(
                            appointment.status ?? "unknown"
                          ).toLowerCase()}`}
                        >
                          {getValue(appointment, ["status"])}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>

      <footer>CareVoice · AI-powered appointment management</footer>
    </div>
  );
}

export default App;
