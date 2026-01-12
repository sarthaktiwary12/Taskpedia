import { NextRequest, NextResponse } from 'next/server';
import { getNodeById, getChildNodes } from '@/lib/data';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;

  try {
    const node = await getNodeById(decodeURIComponent(id));

    if (!node) {
      return NextResponse.json(
        { success: false, error: 'Node not found' },
        { status: 404 }
      );
    }

    const children = await getChildNodes(node.id);

    return NextResponse.json({
      success: true,
      node,
      children,
    });
  } catch (error) {
    console.error('Node API error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch node' },
      { status: 500 }
    );
  }
}
