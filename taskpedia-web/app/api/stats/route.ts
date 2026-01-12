import { NextResponse } from 'next/server';
import { getDatasetStats } from '@/lib/data';

export const revalidate = 3600; // Cache for 1 hour

export async function GET() {
  try {
    const stats = await getDatasetStats();

    return NextResponse.json({
      success: true,
      stats,
    });
  } catch (error) {
    console.error('Stats API error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch stats' },
      { status: 500 }
    );
  }
}
