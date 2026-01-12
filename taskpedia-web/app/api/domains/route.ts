import { NextResponse } from 'next/server';
import { getDomains } from '@/lib/data';

export const revalidate = 3600;

export async function GET() {
  try {
    const domains = await getDomains();

    return NextResponse.json({
      success: true,
      count: domains.length,
      domains,
    });
  } catch (error) {
    console.error('Domains API error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch domains' },
      { status: 500 }
    );
  }
}
