#!/usr/bin/env python3
"""
Skill 4.1: LTV Calculation

计算用户生命周期价值 (LifeTime Value)
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta

# ============================================================
# 1. 数据生成
# ============================================================

def generate_sample_data(n_users: int = 5000, output_path: str = "sample_ltv_data.csv"):
    """
    生成用户付费数据
    """
    np.random.seed(42)
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 6, 1)
    
    users = []
    
    for i in range(n_users):
        user_id = f"user_{i:05d}"
        signup_date = start_date + timedelta(days=np.random.randint(0, 90))
        
        # 用户类型
        plan_type = np.random.choice(['free', 'pro', 'enterprise'], p=[0.6, 0.3, 0.1])
        primary_scenario = np.random.choice(['coding', 'writing', 'data_analysis', 'general_qa'], p=[0.25, 0.30, 0.20, 0.25])
        
        # 是否付费
        if plan_type == 'free':
            is_paid = False
            monthly_spend = 0
        else:
            is_paid = True
            if plan_type == 'pro':
                monthly_spend = np.random.choice([20, 25, 30], p=[0.5, 0.3, 0.2])
            else:
                monthly_spend = np.random.choice([50, 75, 100], p=[0.4, 0.4, 0.2])
        
        # 生命周期（月）
        if np.random.random() < 0.4:
            lifetime_months = np.random.poisson(2) + 1
        else:
            lifetime_months = np.random.poisson(6) + 1
        lifetime_months = min(lifetime_months, 12)
        
        # 流失时间
        churn_date = signup_date + timedelta(days=lifetime_months * 30)
        if churn_date > end_date:
            churn_date = end_date
            is_churned = False
        else:
            is_churned = True
        
        # 计算 LTV
        total_revenue = monthly_spend * lifetime_months
        
        # 使用强度
        sessions_per_month = np.random.poisson(5) + 2
        avg_session_depth = np.random.gamma(2, 2) + 1
        
        users.append({
            'user_id': user_id,
            'signup_date': signup_date.strftime('%Y-%m-%d'),
            'churn_date': churn_date.strftime('%Y-%m-%d'),
            'plan_type': plan_type,
            'primary_scenario': primary_scenario,
            'is_paid': is_paid,
            'monthly_spend': monthly_spend,
            'lifetime_months': lifetime_months,
            'total_revenue': total_revenue,
            'is_churned': is_churned,
            'sessions_per_month': sessions_per_month,
            'avg_session_depth': round(avg_session_depth, 1)
        })
    
    df = pd.DataFrame(users)
    df.to_csv(output_path, index=False)
    print(f"✅ Sample data saved to: {output_path}")
    print(f"   Total users: {len(df)}")
    print(f"   Paid users: {df['is_paid'].sum()}")
    print(f"   Total revenue: ${df['total_revenue'].sum():,.2f}")
    return df


def load_data(file_path: str = "sample_ltv_data.csv"):
    if not os.path.exists(file_path):
        print("📊 Generating sample data...")
        generate_sample_data()
    return pd.read_csv(file_path)


# ============================================================
# 2. LTV 计算
# ============================================================

def calculate_ltv(df):
    """
    计算各种 LTV 指标
    """
    
    # 整体 LTV
    total_users = len(df)
    total_revenue = df['total_revenue'].sum()
    avg_ltv = total_revenue / total_users
    
    # 付费用户 LTV
    paid_users = df[df['is_paid'] == True]
    paid_total = len(paid_users)
    paid_revenue = paid_users['total_revenue'].sum()
    paid_avg_ltv = paid_revenue / paid_total if paid_total > 0 else 0
    
    # 免费用户 LTV
    free_users = df[df['is_paid'] == False]
    free_total = len(free_users)
    free_revenue = free_users['total_revenue'].sum()
    free_avg_ltv = free_revenue / free_total if free_total > 0 else 0
    
    # 月均 ARPU = 平均 LTV / 平均生命周期
    avg_lifetime = df['lifetime_months'].mean()
    monthly_arpu = avg_ltv / avg_lifetime if avg_lifetime > 0 else 0
    
    # 付费率
    paid_rate = paid_total / total_users
    
    # ===== LTV 分段（修正：包含 $0） =====
    ltv_bins = [-0.1, 0, 10, 50, 100, 200, 500, float('inf')]
    ltv_labels = ['$0', '$1-10', '$10-50', '$50-100', '$100-200', '$200-500', '$500+']
    df['ltv_segment'] = pd.cut(df['total_revenue'], bins=ltv_bins, labels=ltv_labels)
    ltv_distribution = df['ltv_segment'].value_counts().sort_index().to_dict()
    
    # 按计划类型分组
    plan_ltv = df.groupby('plan_type').agg({
        'total_revenue': ['sum', 'mean'],
        'user_id': 'count',
        'lifetime_months': 'mean'
    }).round(2)
    plan_ltv.columns = ['总营收', '平均LTV', '用户数', '平均生命周期(月)']
    plan_ltv = plan_ltv.reset_index()
    
    # 按场景分组
    scenario_ltv = df.groupby('primary_scenario').agg({
        'total_revenue': ['sum', 'mean'],
        'user_id': 'count',
        'lifetime_months': 'mean'
    }).round(2)
    scenario_ltv.columns = ['总营收', '平均LTV', '用户数', '平均生命周期(月)']
    scenario_ltv = scenario_ltv.reset_index()
    
    return {
        'total_users': total_users,
        'total_revenue': total_revenue,
        'avg_ltv': avg_ltv,
        'paid_users': paid_total,
        'paid_revenue': paid_revenue,
        'paid_avg_ltv': paid_avg_ltv,
        'free_users': free_total,
        'free_avg_ltv': free_avg_ltv,
        'monthly_arpu': monthly_arpu,
        'paid_rate': paid_rate,
        'avg_lifetime': avg_lifetime,
        'plan_ltv': plan_ltv,
        'scenario_ltv': scenario_ltv,
        'ltv_distribution': ltv_distribution
    }


# ============================================================
# 3. HTML 报告生成
# ============================================================

def generate_html_report(results, output_path="output/ltv_report.html"):
    """生成 LTV 报告"""
    
    # ===== 概览卡片 =====
    overview_cards = f"""
    <div class="stat-grid">
        <div class="stat-card"><div class="label">总用户</div><div class="value">{results['total_users']:,}</div></div>
        <div class="stat-card"><div class="label">总营收</div><div class="value">${results['total_revenue']:,.0f}</div></div>
        <div class="stat-card"><div class="label">平均 LTV</div><div class="value">${results['avg_ltv']:.2f}</div></div>
        <div class="stat-card"><div class="label">付费用户 LTV</div><div class="value">${results['paid_avg_ltv']:.2f}</div></div>
        <div class="stat-card"><div class="label">免费用户 LTV</div><div class="value">${results['free_avg_ltv']:.2f}</div></div>
        <div class="stat-card"><div class="label">月均 ARPU</div><div class="value">${results['monthly_arpu']:.2f}</div></div>
        <div class="stat-card"><div class="label">平均生命周期</div><div class="value">{results['avg_lifetime']:.1f} 月</div></div>
        <div class="stat-card"><div class="label">付费率</div><div class="value">{results['paid_rate']*100:.1f}%</div></div>
    </div>
    """
    
    # ===== 指标关系说明 =====
    relationship_box = f"""
    <div class="relationship-box">
        <strong>📐 指标关系</strong><br>
        平均 LTV × 总用户 = 总营收 &nbsp;→&nbsp; ${results['avg_ltv']:.2f} × {results['total_users']:,} = ${results['total_revenue']:,.0f}<br>
        月均 ARPU = 平均 LTV / 平均生命周期 &nbsp;→&nbsp; ${results['avg_ltv']:.2f} / {results['avg_lifetime']:.1f}月 = ${results['monthly_arpu']:.2f}/月<br>
        付费率 = 付费用户 / 总用户 &nbsp;→&nbsp; {results['paid_users']:,} / {results['total_users']:,} = {results['paid_rate']*100:.1f}%
    </div>
    """
    
    # ===== LTV 分布 =====
    dist_rows = ""
    for segment, count in results['ltv_distribution'].items():
        pct = count / results['total_users'] * 100
        dist_rows += f"""
        <tr><td>{segment}</td><td>{count:,}</td><td>{pct:.1f}%</td></tr>
        """
    
    # ===== 按计划类型 =====
    plan_rows = ""
    for _, row in results['plan_ltv'].iterrows():
        plan_rows += f"""
        <tr>
            <td><strong>{row['plan_type']}</strong></td>
            <td>{int(row['用户数']):,}</td>
            <td>${row['总营收']:,.0f}</td>
            <td>${row['平均LTV']:.2f}</td>
            <td>{row['平均生命周期(月)']:.1f}月</td>
        </tr>
        """
    
    # ===== 按场景 =====
    scenario_rows = ""
    for _, row in results['scenario_ltv'].iterrows():
        scenario_rows += f"""
        <tr>
            <td><strong>{row['primary_scenario']}</strong></td>
            <td>{int(row['用户数']):,}</td>
            <td>${row['总营收']:,.0f}</td>
            <td>${row['平均LTV']:.2f}</td>
            <td>{row['平均生命周期(月)']:.1f}月</td>
        </tr>
        """
    
    html = f'''<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LTV 计算报告 | Skill 4.1</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;padding:40px 20px}}
        .container{{max-width:1200px;margin:0 auto}}
        
        .header{{background:white;border-radius:20px;padding:30px;margin-bottom:30px;text-align:center;box-shadow:0 2px 10px rgba(0,0,0,0.08)}}
        .header h1{{color:#1a1a2e;font-size:2rem}}
        .header .subtitle{{color:#666;margin-top:8px}}
        
        .section{{background:white;border-radius:20px;padding:25px;margin-bottom:30px;box-shadow:0 2px 10px rgba(0,0,0,0.08)}}
        .section h2{{color:#1a1a2e;font-size:1.2rem;margin-bottom:20px;padding-bottom:10px;border-bottom:2px solid #667eea}}
        
        .stat-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px}}
        .stat-card{{background:#f8f9fa;padding:20px;border-radius:16px;text-align:center;border-top:4px solid #667eea}}
        .stat-card .label{{font-size:0.8rem;color:#888}}
        .stat-card .value{{font-size:1.8rem;font-weight:bold;color:#1a1a2e}}
        
        .relationship-box{{background:#f0f4ff;padding:16px 20px;border-radius:12px;border-left:4px solid #667eea;margin-bottom:16px;line-height:1.8;font-size:0.95rem}}
        
        .table-wrapper{{overflow-x:auto}}
        table{{width:100%;border-collapse:collapse;font-size:0.9rem}}
        th,td{{padding:10px 14px;text-align:left;border-bottom:1px solid #eee}}
        th{{background:#f8f9fa;font-weight:600;color:#667eea}}
        tr:hover td{{background:#fafafa}}
        
        .footer{{text-align:center;padding:20px;color:#aaa;font-size:0.8rem}}
        
        @media(max-width:768px){{.stat-grid{{grid-template-columns:repeat(2,1fr)}}}}
    </style>
</head>
<body>
<div class="container">
    
    <div class="header">
        <h1>💰 LTV 计算报告</h1>
        <div class="subtitle">用户生命周期价值分析</div>
    </div>
    
    <!-- ====== 定义说明 ====== -->
    <div class="section">
        <h2>📐 LTV 定义与指标说明</h2>
        <div style="background:#f8f9fa;padding:16px 20px;border-radius:12px;margin-bottom:12px;line-height:1.8;">
            <strong>LTV (LifeTime Value)</strong> = 用户从开始使用到流失/观察期结束，为产品贡献的总价值<br><br>
            <strong>计算公式</strong>：LTV = Σ 用户每月付费 × 生命周期月数<br><br>
            <strong>关键指标</strong>：<br>
            • <strong>平均 LTV</strong> = 总营收 / 总用户数（所有用户的平均贡献）<br>
            • <strong>付费用户 LTV</strong> = 付费用户总营收 / 付费用户数<br>
            • <strong>月均 ARPU</strong> = 平均 LTV / 平均生命周期（每月每用户平均收入）<br>
            • <strong>付费率</strong> = 付费用户数 / 总用户数
        </div>
        {relationship_box}
    </div>
    
    <!-- ====== 概览 ====== -->
    <div class="section">
        <h2>📊 概览</h2>
        {overview_cards}
    </div>
    
    <!-- ====== LTV 分布 ====== -->
    <div class="section">
        <h2>📈 LTV 分布</h2>
        <div class="table-wrapper">
            <table>
                <thead><tr><th>LTV 区间</th><th>用户数</th><th>占比</th></tr></thead>
                <tbody>{dist_rows}</tbody>
            </table>
        </div>
    </div>
    
    <!-- ====== 按计划类型 ====== -->
    <div class="section">
        <h2>📋 按计划类型</h2>
        <div class="table-wrapper">
            <table>
                <thead><tr><th>计划</th><th>用户数</th><th>总营收</th><th>平均 LTV</th><th>平均生命周期</th></tr></thead>
                <tbody>{plan_rows}</tbody>
            </table>
        </div>
    </div>
    
    <!-- ====== 按场景 ====== -->
    <div class="section">
        <h2>📋 按使用场景</h2>
        <div class="table-wrapper">
            <table>
                <thead><tr><th>场景</th><th>用户数</th><th>总营收</th><th>平均 LTV</th><th>平均生命周期</th></tr></thead>
                <tbody>{scenario_rows}</tbody>
            </table>
        </div>
    </div>
    
    <div class="footer">
        <p>Generated by Skill 4.1: LTV Calculation</p>
        <p>LTV = 用户每月付费 × 生命周期月数</p>
    </div>
</div>
</body>
</html>'''
    
    os.makedirs('output', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report saved: {output_path}")
    return output_path


# ============================================================
# 4. 主函数
# ============================================================

def main():
    print("=" * 60)
    print("Skill 4.1: LTV Calculation")
    print("=" * 60)
    
    df = load_data()
    print(f"Loaded {len(df)} users")
    
    print("\n📊 Calculating LTV...")
    results = calculate_ltv(df)
    
    print("\n" + "-" * 50)
    print("LTV RESULTS")
    print("-" * 50)
    print(f"  Total users: {results['total_users']:,}")
    print(f"  Total revenue: ${results['total_revenue']:,.2f}")
    print(f"  Average LTV: ${results['avg_ltv']:.2f}")
    print(f"  Paid users LTV: ${results['paid_avg_ltv']:.2f}")
    print(f"  Free users LTV: ${results['free_avg_ltv']:.2f}")
    print(f"  Monthly ARPU: ${results['monthly_arpu']:.2f}")
    print(f"  Average lifetime: {results['avg_lifetime']:.1f} months")
    print(f"  Paid rate: {results['paid_rate']*100:.1f}%")
    
    print("\n📄 Generating HTML report...")
    report_path = generate_html_report(results)
    
    print("\n" + "=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print(f"\n📁 Open report: {report_path}")


if __name__ == "__main__":
    main()
