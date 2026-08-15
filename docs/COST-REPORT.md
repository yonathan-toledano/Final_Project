# דוח עלויות תחזוקה — Phase 4 Monitor

**נכון ל־:** 2026-08-15T10:13:44Z  
**Region:** `us-east-1`  
**Scope:** תשתית `Final_Project` בלבד. שרת Hermes אינו כלול.

## משאבים פעילים שנבדקו בפועל

| משאב | תצורה | כמות |
|---|---:|---:|
| EC2 | `t3.small`, Linux On-Demand | 1 |
| EBS | `gp3`, ‏16 GB, baseline 3,000 IOPS / 125 MB/s | 1 |
| Public IPv4 | כתובת ציבורית צמודה ל־EC2 | 1 |
| NAT Gateway | לא קיים | 0 |
| Load Balancer | לא קיים | 0 |
| Elastic IP | לא קיים | 0 |
| RDS | לא קיים בפרויקט | 0 |
| EKS | לא קיים בפרויקט | 0 |

## אומדן חודשי

החישוב משתמש ב־730 שעות ממוצעות בחודש.

| רכיב | מחיר יחידה | חישוב | אומדן חודשי |
|---|---:|---:|---:|
| EC2 `t3.small` | $0.0208 לשעה | 730 × $0.0208 | **$15.18** |
| EBS `gp3` | $0.08 ל־GB בחודש | 16 × $0.08 | **$1.28** |
| Public IPv4 | $0.005 לשעה | 730 × $0.005 | **$3.65** |
| **סה״כ בסיסי** |  |  | **$20.11 לחודש** |

## עלות מוערכת עד כה

ה־EC2 הנוכחי הופעל ב־`2026-08-15T07:56:17Z`.

- זמן פעילות שנמדד: כ־2.29 שעות
- עלות מחושבת ל־EC2 + EBS + Public IPv4: **כ־$0.06**

ייתכן חיוב קטן נוסף ממשאבים זמניים שהוחלפו במהלך ההקמה. הוא אינו נכלל בחישוב מפני שלחשבון IAM הנוכחי אין הרשאת `ce:GetCostAndUsage` לצפייה בחשבונית האמיתית.

## שירותים ללא עלות בסיסית נוספת בתצורה הנוכחית

- VPC, subnet, route table ו־Internet Gateway
- K3S
- Helm
- ArgoCD
- Prometheus-style application metrics endpoint
- Cloudflare Tunnel/DNS במסגרת התוכנית הקיימת
- GitHub Actions עבור repository ציבורי, בכפוף למגבלות התוכנית
- Docker Hub, בכפוף למגבלות התוכנית
- HCP Terraform — עדיין לא חובר ולכן אינו מחויב כרגע

## עלויות משתנות שלא נכללו

- Data Transfer Out מעבר למכסה החינמית של AWS
- CPU credits אם `t3.small` במצב Unlimited יעבור לאורך זמן את ביצועי הבסיס
- מסים/VAT
- שינוי לתוכנית בתשלום ב־GitHub, Docker Hub, Cloudflare או HCP Terraform
- snapshots, גיבויים או משאבים עתידיים

## המלצות לשמירת העלות נמוכה

1. להשאיר EC2 יחיד ללא NAT Gateway, ALB, EKS או RDS.
2. לעצור או להשמיד את סביבת ההדגמה כאשר אינה נדרשת לאורך זמן.
3. להגדיר AWS Budget בסך $25 לחודש עם התראות ב־50%, 80% ו־100%.
4. לעקוב אחר CPU לפני מעבר ל־instance גדול יותר.
5. לשקול `t3a.small` רק לאחר בדיקת תאימות וזמינות; הוא מעט זול יותר.

## מקורות מחיר

- [AWS EC2 On-Demand Pricing](https://aws.amazon.com/ec2/pricing/on-demand/)
- [AWS EBS Pricing](https://aws.amazon.com/ebs/pricing/)
- [AWS VPC Public IPv4 Pricing](https://aws.amazon.com/vpc/pricing/)

> זהו אומדן הנדסי, לא חשבונית. לקבלת עלות מדויקת צריך לאפשר ל־IAM קריאת Cost Explorer או לבדוק את AWS Billing Console.
