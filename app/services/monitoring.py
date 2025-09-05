"""Advanced monitoring, analytics, and observability for AI Veterinary Receptionist."""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
from contextlib import asynccontextmanager

from prometheus_client import Counter, Histogram, Gauge, generate_latest
import structlog


@dataclass
class CallMetrics:
    """Metrics for individual calls."""
    call_sid: str
    phone_number: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    intent: Optional[str]
    urgency: str
    final_state: str
    interactions_count: int
    speech_recognition_success: bool
    response_time_ms: float
    escalated: bool
    escalation_reason: Optional[str]
    customer_satisfaction: Optional[int]  # 1-5 scale
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            **asdict(self),
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }


@dataclass
class SystemMetrics:
    """System-wide performance metrics."""
    timestamp: datetime
    active_calls: int
    total_calls_today: int
    average_response_time_ms: float
    speech_recognition_accuracy: float
    system_uptime_hours: float
    cpu_usage_percent: float
    memory_usage_percent: float
    error_rate_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat()
        }


class AdvancedMonitoring:
    """Advanced monitoring and analytics system."""
    
    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.start_time = datetime.now()
        
        # Prometheus metrics
        self.call_counter = Counter(
            'vet_ai_calls_total',
            'Total number of calls',
            ['intent', 'urgency', 'outcome']
        )
        
        self.response_time_histogram = Histogram(
            'vet_ai_response_time_seconds',
            'Response time in seconds',
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )
        
        self.active_calls_gauge = Gauge(
            'vet_ai_active_calls',
            'Number of active calls'
        )
        
        self.speech_accuracy_gauge = Gauge(
            'vet_ai_speech_accuracy',
            'Speech recognition accuracy percentage'
        )
        
        self.error_counter = Counter(
            'vet_ai_errors_total',
            'Total number of errors',
            ['error_type', 'endpoint']
        )
        
        # In-memory storage for recent metrics
        self.call_metrics: Dict[str, CallMetrics] = {}
        self.system_metrics_history: deque = deque(maxlen=1000)
        self.error_log: deque = deque(maxlen=500)
        
        # Real-time analytics
        self.hourly_stats = defaultdict(lambda: {
            'total_calls': 0,
            'emergency_calls': 0,
            'appointment_requests': 0,
            'health_inquiries': 0,
            'escalations': 0,
            'average_duration': 0.0,
            'customer_satisfaction': 0.0
        })
        
        # Performance tracking
        self.response_times = deque(maxlen=100)
        self.speech_recognition_results = deque(maxlen=100)
        
        # Thread-safe locks
        self._metrics_lock = threading.Lock()
        
        # Start background monitoring
        self._start_background_monitoring()
    
    def start_call_monitoring(self, call_sid: str, phone_number: str) -> None:
        """Start monitoring a new call."""
        with self._metrics_lock:
            self.call_metrics[call_sid] = CallMetrics(
                call_sid=call_sid,
                phone_number=phone_number,
                start_time=datetime.now(),
                end_time=None,
                duration_seconds=None,
                intent=None,
                urgency="unknown",
                final_state="started",
                interactions_count=0,
                speech_recognition_success=False,
                response_time_ms=0.0,
                escalated=False,
                escalation_reason=None,
                customer_satisfaction=None
            )
            
            self.active_calls_gauge.inc()
            self.logger.info("Call monitoring started", call_sid=call_sid, phone=phone_number)
    
    def update_call_metrics(self, call_sid: str, **kwargs) -> None:
        """Update metrics for an ongoing call."""
        with self._metrics_lock:
            if call_sid in self.call_metrics:
                metrics = self.call_metrics[call_sid]
                
                for key, value in kwargs.items():
                    if hasattr(metrics, key):
                        setattr(metrics, key, value)
                
                self.logger.debug("Call metrics updated", call_sid=call_sid, updates=kwargs)
    
    def end_call_monitoring(self, call_sid: str, final_state: str) -> None:
        """End monitoring for a call and record final metrics."""
        with self._metrics_lock:
            if call_sid not in self.call_metrics:
                return
            
            metrics = self.call_metrics[call_sid]
            metrics.end_time = datetime.now()
            metrics.duration_seconds = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.final_state = final_state
            
            # Update Prometheus metrics
            self.call_counter.labels(
                intent=metrics.intent or "unknown",
                urgency=metrics.urgency,
                outcome=final_state
            ).inc()
            
            self.active_calls_gauge.dec()
            
            # Update hourly statistics
            hour_key = metrics.start_time.strftime("%Y-%m-%d-%H")
            self.hourly_stats[hour_key]['total_calls'] += 1
            
            if metrics.intent == "emergency":
                self.hourly_stats[hour_key]['emergency_calls'] += 1
            elif metrics.intent in ["appointment_new", "appointment_modify"]:
                self.hourly_stats[hour_key]['appointment_requests'] += 1
            elif metrics.intent == "health_question":
                self.hourly_stats[hour_key]['health_inquiries'] += 1
            
            if metrics.escalated:
                self.hourly_stats[hour_key]['escalations'] += 1
            
            self.logger.info(
                "Call monitoring completed",
                call_sid=call_sid,
                duration=metrics.duration_seconds,
                intent=metrics.intent,
                outcome=final_state
            )
    
    def record_response_time(self, response_time_ms: float) -> None:
        """Record a response time measurement."""
        with self._metrics_lock:
            self.response_times.append(response_time_ms)
            self.response_time_histogram.observe(response_time_ms / 1000.0)
    
    def record_speech_recognition(self, success: bool, confidence: float = 0.0) -> None:
        """Record speech recognition result."""
        with self._metrics_lock:
            self.speech_recognition_results.append((success, confidence))
            
            # Update accuracy gauge
            if len(self.speech_recognition_results) > 0:
                accuracy = sum(1 for s, _ in self.speech_recognition_results if s) / len(self.speech_recognition_results)
                self.speech_accuracy_gauge.set(accuracy * 100)
    
    def record_error(self, error_type: str, endpoint: str, error_details: str) -> None:
        """Record an error occurrence."""
        with self._metrics_lock:
            self.error_counter.labels(error_type=error_type, endpoint=endpoint).inc()
            
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "endpoint": endpoint,
                "details": error_details
            }
            
            self.error_log.append(error_record)
            
            self.logger.error(
                "Error recorded",
                error_type=error_type,
                endpoint=endpoint,
                details=error_details
            )
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics."""
        with self._metrics_lock:
            active_calls = len([m for m in self.call_metrics.values() if m.end_time is None])
            
            # Calculate averages
            avg_response_time = 0.0
            if self.response_times:
                avg_response_time = sum(self.response_times) / len(self.response_times)
            
            speech_accuracy = 0.0
            if self.speech_recognition_results:
                successful = sum(1 for s, _ in self.speech_recognition_results if s)
                speech_accuracy = (successful / len(self.speech_recognition_results)) * 100
            
            # Get today's call count
            today = datetime.now().strftime("%Y-%m-%d")
            today_calls = sum(
                stats['total_calls'] 
                for hour_key, stats in self.hourly_stats.items()
                if hour_key.startswith(today)
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "active_calls": active_calls,
                "total_calls_today": today_calls,
                "average_response_time_ms": avg_response_time,
                "speech_recognition_accuracy": speech_accuracy,
                "system_uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
                "recent_errors": len(self.error_log),
                "hourly_breakdown": dict(self.hourly_stats)
            }
    
    def get_call_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get call analytics for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._metrics_lock:
            recent_calls = [
                metrics for metrics in self.call_metrics.values()
                if metrics.start_time >= cutoff_time
            ]
            
            if not recent_calls:
                return {"message": "No calls in the specified time period"}
            
            # Calculate analytics
            total_calls = len(recent_calls)
            completed_calls = [c for c in recent_calls if c.end_time is not None]
            
            intent_breakdown = defaultdict(int)
            urgency_breakdown = defaultdict(int)
            outcome_breakdown = defaultdict(int)
            
            total_duration = 0.0
            escalation_count = 0
            
            for call in recent_calls:
                if call.intent:
                    intent_breakdown[call.intent] += 1
                urgency_breakdown[call.urgency] += 1
                outcome_breakdown[call.final_state] += 1
                
                if call.duration_seconds:
                    total_duration += call.duration_seconds
                
                if call.escalated:
                    escalation_count += 1
            
            avg_duration = total_duration / len(completed_calls) if completed_calls else 0
            escalation_rate = (escalation_count / total_calls) * 100 if total_calls > 0 else 0
            
            return {
                "time_period_hours": hours,
                "total_calls": total_calls,
                "completed_calls": len(completed_calls),
                "average_duration_seconds": avg_duration,
                "escalation_rate_percent": escalation_rate,
                "intent_breakdown": dict(intent_breakdown),
                "urgency_breakdown": dict(urgency_breakdown),
                "outcome_breakdown": dict(outcome_breakdown),
                "top_escalation_reasons": self._get_top_escalation_reasons(recent_calls)
            }
    
    def _get_top_escalation_reasons(self, calls: List[CallMetrics]) -> List[Dict[str, Any]]:
        """Get the most common escalation reasons."""
        escalation_reasons = defaultdict(int)
        
        for call in calls:
            if call.escalated and call.escalation_reason:
                escalation_reasons[call.escalation_reason] += 1
        
        return [
            {"reason": reason, "count": count}
            for reason, count in sorted(escalation_reasons.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        real_time = self.get_real_time_metrics()
        analytics_24h = self.get_call_analytics(24)
        analytics_7d = self.get_call_analytics(168)  # 7 days
        
        return {
            "report_generated": datetime.now().isoformat(),
            "real_time_metrics": real_time,
            "last_24_hours": analytics_24h,
            "last_7_days": analytics_7d,
            "system_health": self._get_system_health(),
            "recommendations": self._generate_recommendations(real_time, analytics_24h)
        }
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health indicators."""
        with self._metrics_lock:
            recent_errors = len([
                error for error in self.error_log
                if datetime.fromisoformat(error["timestamp"]) > datetime.now() - timedelta(hours=1)
            ])
            
            health_score = 100
            health_issues = []
            
            # Check error rate
            if recent_errors > 10:
                health_score -= 20
                health_issues.append("High error rate in the last hour")
            
            # Check response times
            if self.response_times:
                avg_response = sum(self.response_times) / len(self.response_times)
                if avg_response > 2000:  # 2 seconds
                    health_score -= 15
                    health_issues.append("Slow response times detected")
            
            # Check speech recognition accuracy
            if self.speech_recognition_results:
                accuracy = sum(1 for s, _ in self.speech_recognition_results if s) / len(self.speech_recognition_results)
                if accuracy < 0.8:  # 80%
                    health_score -= 25
                    health_issues.append("Low speech recognition accuracy")
            
            health_status = "excellent" if health_score >= 90 else "good" if health_score >= 70 else "degraded" if health_score >= 50 else "critical"
            
            return {
                "health_score": health_score,
                "health_status": health_status,
                "issues": health_issues,
                "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
                "recent_errors_count": recent_errors
            }
    
    def _generate_recommendations(self, real_time: Dict, analytics: Dict) -> List[str]:
        """Generate actionable recommendations based on metrics."""
        recommendations = []
        
        # Response time recommendations
        if real_time.get("average_response_time_ms", 0) > 1500:
            recommendations.append("Consider optimizing response time - current average is above 1.5 seconds")
        
        # Speech accuracy recommendations
        if real_time.get("speech_recognition_accuracy", 100) < 85:
            recommendations.append("Speech recognition accuracy below 85% - consider adjusting language model or noise filtering")
        
        # Escalation rate recommendations
        escalation_rate = analytics.get("escalation_rate_percent", 0)
        if escalation_rate > 15:
            recommendations.append(f"High escalation rate ({escalation_rate:.1f}%) - review AI conversation flows")
        
        # Volume recommendations
        if analytics.get("total_calls", 0) > 100:
            recommendations.append("High call volume detected - consider adding more concurrent processing capacity")
        
        return recommendations
    
    def _start_background_monitoring(self):
        """Start background monitoring tasks."""
        def monitor_system():
            while True:
                try:
                    # Record system metrics every minute
                    metrics = SystemMetrics(
                        timestamp=datetime.now(),
                        active_calls=len([m for m in self.call_metrics.values() if m.end_time is None]),
                        total_calls_today=0,  # Would be calculated from database
                        average_response_time_ms=sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                        speech_recognition_accuracy=0.0,  # Would be calculated
                        system_uptime_hours=(datetime.now() - self.start_time).total_seconds() / 3600,
                        cpu_usage_percent=0.0,  # Would use psutil
                        memory_usage_percent=0.0,  # Would use psutil
                        error_rate_percent=0.0  # Would be calculated
                    )
                    
                    self.system_metrics_history.append(metrics)
                    
                    # Clean up old metrics (older than 7 days)
                    cutoff_time = datetime.now() - timedelta(days=7)
                    expired_calls = [
                        call_sid for call_sid, metrics in self.call_metrics.items()
                        if metrics.end_time and metrics.end_time < cutoff_time
                    ]
                    
                    for call_sid in expired_calls:
                        del self.call_metrics[call_sid]
                    
                    time.sleep(60)  # Monitor every minute
                    
                except Exception as e:
                    self.logger.error("Background monitoring error", error=str(e))
                    time.sleep(60)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format."""
        return generate_latest()
    
    @asynccontextmanager
    async def track_request(self, endpoint: str):
        """Context manager to track request performance."""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            self.record_error("request_error", endpoint, str(e))
            raise
        finally:
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            self.record_response_time(response_time_ms)


# Global monitoring instance
monitoring = AdvancedMonitoring()
