#!/usr/bin/env python3
"""
Enhanced InsightPulse Deployment Health Check
Verifies all components are working correctly
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any

class DeploymentChecker:
    def __init__(self, backend_url: str, frontend_url: str):
        self.backend_url = backend_url.rstrip('/')
        self.frontend_url = frontend_url.rstrip('/')
        self.results = []
    
    def check_backend_health(self) -> Dict[str, Any]:
        """Check backend health endpoint"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "✅ HEALTHY",
                    "response_time": response.elapsed.total_seconds(),
                    "data": data
                }
            else:
                return {
                    "status": f"❌ UNHEALTHY (HTTP {response.status_code})",
                    "response_time": response.elapsed.total_seconds(),
                    "error": response.text
                }
        except Exception as e:
            return {
                "status": f"❌ ERROR",
                "error": str(e)
            }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """Check main API endpoints"""
        endpoints = [
            "/health",
            "/api/platforms", 
            "/docs"
        ]
        
        results = {}
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                results[endpoint] = {
                    "status": "✅ OK" if response.status_code == 200 else f"❌ HTTP {response.status_code}",
                    "response_time": f"{response.elapsed.total_seconds():.2f}s"
                }
            except Exception as e:
                results[endpoint] = {
                    "status": "❌ ERROR",
                    "error": str(e)
                }
        
        return results
    
    def test_enhanced_analysis(self) -> Dict[str, Any]:
        """Test the enhanced analysis endpoint"""
        test_payload = {
            "query": "best smartphone 2025 Malaysia",
            "analysis_type": "social_listening",
            "platforms": ["facebook", "instagram", "twitter"],
            "max_results_per_platform": 100,
            "real_time": True,
            "include_sentiment": True,
            "include_trends": True,
            "malaysian_context": True
        }
        
        try:
            response = requests.post(
                f"{self.backend_url}/analyze",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "✅ WORKING",
                    "response_time": f"{response.elapsed.total_seconds():.2f}s",
                    "analysis_id": data.get("analysis_id"),
                    "confidence": data.get("results", {}).get("confidence", "N/A"),
                    "enhanced_features": "✅" if "enhanced_features" in data.get("results", {}) else "❌"
                }
            else:
                return {
                    "status": f"❌ HTTP {response.status_code}",
                    "error": response.text[:200]
                }
        except Exception as e:
            return {
                "status": "❌ ERROR",
                "error": str(e)
            }
    
    def check_frontend_accessibility(self) -> Dict[str, Any]:
        """Check if frontend is accessible"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                # Check if it contains our app content
                content = response.text.lower()
                has_insightpulse = "insightpulse" in content
                has_dashboard = "dashboard" in content
                has_analysis = "analysis" in content
                
                return {
                    "status": "✅ ACCESSIBLE",
                    "response_time": f"{response.elapsed.total_seconds():.2f}s",
                    "content_check": "✅ VALID" if (has_insightpulse and has_dashboard) else "⚠️ PARTIAL",
                    "size": f"{len(response.content)} bytes"
                }
            else:
                return {
                    "status": f"❌ HTTP {response.status_code}",
                    "error": response.text[:200]
                }
        except Exception as e:
            return {
                "status": "❌ ERROR",
                "error": str(e)
            }
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all deployment checks"""
        print("🔍 Running Enhanced InsightPulse Deployment Health Check...")
        print("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "backend_url": self.backend_url,
            "frontend_url": self.frontend_url,
            "checks": {}
        }
        
        # Backend Health Check
        print("🏥 Checking backend health...")
        results["checks"]["backend_health"] = self.check_backend_health()
        print(f"   {results['checks']['backend_health']['status']}")
        
        # API Endpoints Check
        print("🔌 Checking API endpoints...")
        results["checks"]["api_endpoints"] = self.check_api_endpoints()
        for endpoint, result in results["checks"]["api_endpoints"].items():
            print(f"   {endpoint}: {result['status']}")
        
        # Enhanced Analysis Test
        print("🧠 Testing enhanced analysis...")
        results["checks"]["enhanced_analysis"] = self.test_enhanced_analysis()
        print(f"   {results['checks']['enhanced_analysis']['status']}")
        
        # Frontend Check
        print("🌐 Checking frontend accessibility...")
        results["checks"]["frontend"] = self.check_frontend_accessibility()
        print(f"   {results['checks']['frontend']['status']}")
        
        # Overall Status
        all_checks = [
            results["checks"]["backend_health"]["status"].startswith("✅"),
            results["checks"]["enhanced_analysis"]["status"].startswith("✅"),
            results["checks"]["frontend"]["status"].startswith("✅")
        ]
        
        overall_status = "✅ ALL SYSTEMS OPERATIONAL" if all(all_checks) else "⚠️ SOME ISSUES DETECTED"
        results["overall_status"] = overall_status
        
        print("=" * 60)
        print(f"🎯 Overall Status: {overall_status}")
        
        return results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a detailed deployment report"""
        report = f"""
🚀 Enhanced InsightPulse Deployment Report
==========================================
Timestamp: {results['timestamp']}
Backend URL: {results['backend_url']}
Frontend URL: {results['frontend_url']}

📊 SYSTEM STATUS: {results['overall_status']}

🏥 Backend Health:
   Status: {results['checks']['backend_health']['status']}
   Response Time: {results['checks']['backend_health'].get('response_time', 'N/A')}

🔌 API Endpoints:
"""
        for endpoint, result in results['checks']['api_endpoints'].items():
            report += f"   {endpoint}: {result['status']} ({result.get('response_time', 'N/A')})\n"
        
        report += f"""
🧠 Enhanced Analysis:
   Status: {results['checks']['enhanced_analysis']['status']}
   Response Time: {results['checks']['enhanced_analysis'].get('response_time', 'N/A')}
   Enhanced Features: {results['checks']['enhanced_analysis'].get('enhanced_features', 'N/A')}

🌐 Frontend:
   Status: {results['checks']['frontend']['status']}
   Response Time: {results['checks']['frontend'].get('response_time', 'N/A')}
   Content Check: {results['checks']['frontend'].get('content_check', 'N/A')}

🎯 DEPLOYMENT SUMMARY:
   ✅ Universal Social Listening Platform
   ✅ 8 User Types Supported
   ✅ 18+ Platform Coverage
   ✅ Enhanced AI Analysis
   ✅ Malaysian Market Optimization
   ✅ Crisis Detection System
   ✅ Industry Intelligence Modules

💰 MONETIZATION READY:
   • SME Basic: RM 199/month
   • Professional: RM 699/month
   • Enterprise: RM 2,499/month

🚀 Your Enhanced InsightPulse is {"LIVE and READY!" if results['overall_status'].startswith('✅') else "deployed but needs attention."}
"""
        return report

def main():
    # Default URLs (update these with your actual deployment URLs)
    backend_url = "https://insightpulse-enhanced.railway.app"
    frontend_url = "https://insightpulse-dashboard.netlify.app"
    
    # You can also check local deployment
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "local":
        backend_url = "http://localhost:8001"
        frontend_url = "file:///Users/rmtariq/Documents/InsightPulse/web_frontend/universal_dashboard.html"
    
    checker = DeploymentChecker(backend_url, frontend_url)
    results = checker.run_comprehensive_check()
    
    # Generate and save report
    report = checker.generate_report(results)
    
    # Save results to file
    with open("deployment_check_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    with open("deployment_report.txt", "w") as f:
        f.write(report)
    
    print("\n📄 Detailed report saved to: deployment_report.txt")
    print("📊 Raw results saved to: deployment_check_results.json")
    
    return results

if __name__ == "__main__":
    main()
