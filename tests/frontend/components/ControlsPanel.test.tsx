import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import ControlsPanel from '../../../frontend/src/components/ControlsPanel';
import controlClient from '../../../frontend/src/api/controlClient';
import { useWorkspaceStore } from '../../../frontend/src/store/useWorkspaceStore';

describe('ControlsPanel', () => {
  beforeEach(() => {
    useWorkspaceStore.setState({ status: 'idle', model: 'o4-mini' });
  });

  it('invokes run and pause controls and toggles disabled state', async () => {
    vi.spyOn(controlClient, 'run').mockResolvedValue();
    vi.spyOn(controlClient, 'pause').mockResolvedValue();
    render(<ControlsPanel workspaceId="ws1" />);

    const runBtn = screen.getByText('Run') as HTMLButtonElement;
    const pauseBtn = screen.getByText('Pause') as HTMLButtonElement;

    expect(runBtn.disabled).toBe(false);
    await act(async () => {
      await fireEvent.click(runBtn);
    });
    expect(controlClient.run).toHaveBeenCalledWith('ws1');
    expect(runBtn.disabled).toBe(true);
    expect(pauseBtn.disabled).toBe(false);

    await act(async () => {
      await fireEvent.click(pauseBtn);
    });
    expect(controlClient.pause).toHaveBeenCalledWith('ws1');
    expect(pauseBtn.disabled).toBe(true);
  });

  it('changes model selection', async () => {
    vi.spyOn(controlClient, 'selectModel').mockResolvedValue();
    render(<ControlsPanel workspaceId="ws1" />);
    const select = screen.getByDisplayValue('o4-mini') as HTMLSelectElement;
    await act(async () => {
      await fireEvent.change(select, { target: { value: 'o3' } });
    });
    expect(controlClient.selectModel).toHaveBeenCalledWith('ws1', 'o3');
  });
});
