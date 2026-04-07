import React, { createContext, useState, useEffect } from 'react'
import axios from 'axios'

export const SystemContext = createContext()

export const SystemProvider = ({ children }) => {
  const [systemState, setSystemState] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [events, setEvents] = useState([])

  useEffect(() => {
    const fetchSystemState = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:9000/system/now')
        setSystemState(response.data)
        setLoading(false)
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }

    fetchSystemState()
    const interval = setInterval(fetchSystemState, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <SystemContext.Provider value={{ systemState, loading, error, events }}>
      {children}
    </SystemContext.Provider>
  )
}
