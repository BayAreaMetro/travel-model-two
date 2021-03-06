/*
 * JPPF.
 * Copyright (C) 2005-2010 JPPF Team.
 * http://www.jppf.org
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.jppf.comm.recovery;

import java.util.EventListener;

/**
 * Listener interface for objects that wish to be notified of broken connection events.
 * @author Laurent Cohen
 */
public interface ReaperListener extends EventListener
{
	/**
	 * Called when the {@link Reaper} detects that a connection is broken. 
	 * @param event encapsulates the server-side connection to a remote peer.
	 */
	void connectionFailed(ReaperEvent event);
}
