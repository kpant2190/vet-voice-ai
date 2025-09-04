import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './index.css';

function App() {
  const [appointments, setAppointments] = useState([]);
  const [clinics, setClinics] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch appointments
      const appointmentsResponse = await axios.get('/api/appointments?limit=10');
      setAppointments(appointmentsResponse.data);

      // Fetch clinics
      const clinicsResponse = await axios.get('/api/clinics');
      setClinics(clinicsResponse.data);

      // Calculate basic stats
      const totalAppointments = appointmentsResponse.data.length;
      const pendingAppointments = appointmentsResponse.data.filter(
        apt => apt.status === 'pending'
      ).length;

      setStats({
        totalClinics: clinicsResponse.data.length,
        totalAppointments,
        pendingAppointments,
        confirmedAppointments: totalAppointments - pendingAppointments
      });

    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateAppointmentStatus = async (appointmentId, newStatus) => {
    try {
      await axios.put(`/api/appointments/${appointmentId}`, {
        status: newStatus
      });
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error updating appointment:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadgeClass = (status) => {
    const baseClass = 'status-badge';
    switch (status) {
      case 'pending':
        return `${baseClass} status-pending`;
      case 'confirmed':
        return `${baseClass} status-confirmed`;
      case 'cancelled':
        return `${baseClass} status-cancelled`;
      case 'completed':
        return `${baseClass} status-completed`;
      default:
        return baseClass;
    }
  };

  if (loading) {
    return (
      <div>
        <div className="header">
          <div className="container">
            <h1>🏥 Vet Voice AI - Admin Dashboard</h1>
          </div>
        </div>
        <div className="container">
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="header">
        <div className="container">
          <h1>🏥 Vet Voice AI - Admin Dashboard</h1>
        </div>
      </div>

      <div className="container">
        {/* Stats Dashboard */}
        <div className="dashboard-grid">
          <div className="card">
            <h3>📊 Total Clinics</h3>
            <div className="stat-number">{stats.totalClinics}</div>
          </div>
          
          <div className="card">
            <h3>📅 Total Appointments</h3>
            <div className="stat-number">{stats.totalAppointments}</div>
          </div>
          
          <div className="card">
            <h3>⏳ Pending Appointments</h3>
            <div className="stat-number">{stats.pendingAppointments}</div>
          </div>
          
          <div className="card">
            <h3>✅ Confirmed Appointments</h3>
            <div className="stat-number">{stats.confirmedAppointments}</div>
          </div>
        </div>

        {/* Recent Appointments */}
        <div className="card">
          <h3>📋 Recent Appointments</h3>
          {appointments.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Pet Name</th>
                  <th>Owner</th>
                  <th>Phone</th>
                  <th>Date & Time</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {appointments.map(appointment => (
                  <tr key={appointment.id}>
                    <td>{appointment.pet_name}</td>
                    <td>{appointment.owner_name}</td>
                    <td>{appointment.owner_phone}</td>
                    <td>{formatDate(appointment.appointment_date)}</td>
                    <td>{appointment.appointment_type}</td>
                    <td>
                      <span className={getStatusBadgeClass(appointment.status)}>
                        {appointment.status}
                      </span>
                    </td>
                    <td>
                      {appointment.status === 'pending' && (
                        <>
                          <button
                            className="btn btn-success"
                            onClick={() => updateAppointmentStatus(appointment.id, 'confirmed')}
                          >
                            Confirm
                          </button>
                          <button
                            className="btn btn-danger"
                            onClick={() => updateAppointmentStatus(appointment.id, 'cancelled')}
                          >
                            Cancel
                          </button>
                        </>
                      )}
                      {appointment.status === 'confirmed' && (
                        <button
                          className="btn"
                          onClick={() => updateAppointmentStatus(appointment.id, 'completed')}
                        >
                          Mark Complete
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No appointments found.</p>
          )}
        </div>

        {/* Registered Clinics */}
        <div className="card">
          <h3>🏥 Registered Clinics</h3>
          {clinics.length > 0 ? (
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Phone</th>
                  <th>Email</th>
                  <th>AI Enabled</th>
                  <th>Auto Booking</th>
                </tr>
              </thead>
              <tbody>
                {clinics.map(clinic => (
                  <tr key={clinic.id}>
                    <td>{clinic.name}</td>
                    <td>{clinic.phone_number}</td>
                    <td>{clinic.email}</td>
                    <td>{clinic.ai_enabled ? '✅' : '❌'}</td>
                    <td>{clinic.auto_booking_enabled ? '✅' : '❌'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>No clinics registered yet.</p>
          )}
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: '40px', color: '#7f8c8d' }}>
          <p>🤖 Vet Voice AI Dashboard - Powered by FastAPI & React</p>
        </div>
      </div>
    </div>
  );
}

export default App;
